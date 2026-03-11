"""Billing: Stripe Checkout and webhooks for Pro subscriptions."""

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from src.config import settings
from src.db import execute, fetch_one
from src.dependencies import get_current_user_id

router = APIRouter(prefix="/billing", tags=["billing"])


def _stripe_configured() -> bool:
    return bool(
        settings.stripe_secret_key
        and settings.stripe_webhook_secret
        and settings.stripe_price_id_monthly
        and settings.stripe_price_id_yearly
    )


async def _downgrade_customer_to_free(customer_id: str) -> None:
    """Set tier to free for the user associated with this Stripe customer."""
    row = await fetch_one(
        "SELECT user_id FROM account_tiers WHERE stripe_customer_id = $1",
        customer_id,
    )
    if row:
        await execute(
            "UPDATE account_tiers SET tier = 'free' WHERE user_id = $1",
            row["user_id"],
        )


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    url: str


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    user_id: str = Depends(get_current_user_id),
) -> PortalResponse:
    """Create a Stripe Customer Portal session. Returns URL for managing subscription."""
    if not _stripe_configured():
        raise HTTPException(status_code=503, detail="Billing not available.")

    row = await fetch_one(
        "SELECT stripe_customer_id FROM account_tiers WHERE user_id = $1",
        user_id,
    )
    customer_id = (
        row["stripe_customer_id"] if row and row["stripe_customer_id"] else None
    )
    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account. Run 'bossa billing upgrade' first.",
        )

    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=settings.bossa_billing_success_url,
    )
    if not session.url:
        raise HTTPException(status_code=500, detail="Failed to create portal session")
    return PortalResponse(url=session.url)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    user_id: str = Depends(get_current_user_id),
    interval: str = Query("month", description="month or year"),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for Pro subscription. Returns URL to redirect user."""
    if not _stripe_configured():
        raise HTTPException(status_code=503, detail="Billing not available.")

    interval = interval.lower()
    if interval not in ("month", "year"):
        raise HTTPException(
            status_code=400, detail="interval must be 'month' or 'year'"
        )

    price_id = (
        settings.stripe_price_id_yearly
        if interval == "year"
        else settings.stripe_price_id_monthly
    )

    stripe.api_key = settings.stripe_secret_key

    # Look up existing Stripe customer from account_tiers
    row = await fetch_one(
        "SELECT stripe_customer_id FROM account_tiers WHERE user_id = $1",
        user_id,
    )
    customer_id = (
        row["stripe_customer_id"] if row and row["stripe_customer_id"] else None
    )

    if not customer_id:
        customer = stripe.Customer.create(metadata={"user_id": user_id})
        customer_id = customer.id
        await execute(
            """
            INSERT INTO account_tiers (user_id, tier, stripe_customer_id)
            VALUES ($1, 'free', $2)
            ON CONFLICT (user_id) DO UPDATE SET stripe_customer_id = $2
            """,
            user_id,
            customer_id,
        )

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer=customer_id,
        client_reference_id=user_id,
        success_url=f"{settings.bossa_billing_success_url}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=settings.bossa_billing_cancel_url,
    )

    if not session.url:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

    return CheckoutResponse(checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Handle Stripe webhook events. Requires raw body for signature verification."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Billing not available.")

    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload") from e
    except stripe.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    event_type = event["type"]
    data = event.get("data", {})
    obj = data.get("object", {})

    if event_type == "checkout.session.completed":
        user_id = obj.get("client_reference_id")
        customer_id = obj.get("customer")
        if user_id and customer_id:
            await execute(
                """
                INSERT INTO account_tiers (user_id, tier, stripe_customer_id)
                VALUES ($1, 'pro', $2)
                ON CONFLICT (user_id) DO UPDATE SET tier = 'pro', stripe_customer_id = $2
                """,
                user_id,
                customer_id,
            )

    elif event_type == "customer.subscription.updated":
        status = obj.get("status")
        if status in ("canceled", "unpaid", "past_due"):
            customer_id = obj.get("customer")
            if customer_id:
                await _downgrade_customer_to_free(customer_id)

    elif event_type == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        if customer_id:
            await _downgrade_customer_to_free(customer_id)

    return {"status": "success"}
