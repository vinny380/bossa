"""Tests for billing API (Stripe Checkout and webhooks)."""

from unittest.mock import MagicMock, patch

import pytest
import stripe
from httpx import ASGITransport, AsyncClient
from src.dependencies import get_current_user_id
from src.main import app

TEST_USER_ID = "00000000-0000-0000-0000-000000000002"


@pytest.fixture
def stripe_config(monkeypatch):
    """Set Stripe config for tests."""
    monkeypatch.setattr("src.api.billing.settings.stripe_secret_key", "sk_test_xxx")
    monkeypatch.setattr("src.api.billing.settings.stripe_webhook_secret", "whsec_xxx")
    monkeypatch.setattr(
        "src.api.billing.settings.stripe_price_id_monthly", "price_monthly_xxx"
    )
    monkeypatch.setattr(
        "src.api.billing.settings.stripe_price_id_yearly", "price_yearly_xxx"
    )


def _clear_stripe_config(monkeypatch):
    """Ensure Stripe is not configured for 503 tests."""
    monkeypatch.setattr("src.api.billing.settings.stripe_secret_key", "")
    monkeypatch.setattr("src.api.billing.settings.stripe_webhook_secret", "")
    monkeypatch.setattr("src.api.billing.settings.stripe_price_id_monthly", "")
    monkeypatch.setattr("src.api.billing.settings.stripe_price_id_yearly", "")


@pytest.mark.asyncio
async def test_portal_returns_503_when_stripe_not_configured(monkeypatch) -> None:
    """POST /billing/portal returns 503 when Stripe keys not set."""
    _clear_stripe_config(monkeypatch)

    async def override_get_current_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer fake-jwt"},
        ) as client:
            response = await client.post("/api/v1/billing/portal")
        assert response.status_code == 503
        assert "Billing not available" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_portal_returns_400_when_no_billing_account(stripe_config) -> None:
    """POST /billing/portal returns 400 when user has no stripe_customer_id."""

    async def override_get_current_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    async def mock_fetch_one(query, *args):
        return None  # No account_tiers row or no stripe_customer_id

    with patch("src.api.billing.fetch_one", side_effect=mock_fetch_one):
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                headers={"Authorization": "Bearer fake-jwt"},
            ) as client:
                response = await client.post("/api/v1/billing/portal")
            assert response.status_code == 400
            assert "No billing account" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_portal_returns_url_when_configured(stripe_config) -> None:
    """POST /billing/portal returns url when Stripe configured and customer exists."""

    async def override_get_current_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    mock_session = MagicMock()
    mock_session.url = "https://billing.stripe.com/test-portal"

    async def mock_fetch_one(query, *args):
        if "stripe_customer_id" in query:
            return {"stripe_customer_id": "cus_existing"}
        return None

    with (
        patch(
            "src.api.billing.stripe.billing_portal.Session.create",
            return_value=mock_session,
        ),
        patch("src.api.billing.fetch_one", side_effect=mock_fetch_one),
    ):
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                headers={"Authorization": "Bearer fake-jwt"},
            ) as client:
                response = await client.post("/api/v1/billing/portal")
            assert response.status_code == 200
            data = response.json()
            assert data["url"] == "https://billing.stripe.com/test-portal"
        finally:
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_checkout_returns_503_when_stripe_not_configured(monkeypatch) -> None:
    """POST /billing/checkout returns 503 when Stripe keys not set."""
    _clear_stripe_config(monkeypatch)

    async def override_get_current_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer fake-jwt"},
        ) as client:
            response = await client.post(
                "/api/v1/billing/checkout",
                params={"interval": "month"},
            )
        assert response.status_code == 503
        assert "Billing not available" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_checkout_returns_url_when_configured(stripe_config) -> None:
    """POST /billing/checkout returns checkout_url when Stripe configured."""

    async def override_get_current_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test-session"

    # Mock fetch_one to return existing customer so we skip Customer.create and DB insert
    async def mock_fetch_one(query, *args):
        if "stripe_customer_id" in query:
            return {"stripe_customer_id": "cus_existing"}
        return None

    with (
        patch(
            "src.api.billing.stripe.checkout.Session.create", return_value=mock_session
        ),
        patch("src.api.billing.fetch_one", side_effect=mock_fetch_one),
    ):
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                headers={"Authorization": "Bearer fake-jwt"},
            ) as client:
                response = await client.post(
                    "/api/v1/billing/checkout",
                    params={"interval": "month"},
                )
            assert response.status_code == 200
            data = response.json()
            assert data["checkout_url"] == "https://checkout.stripe.com/test-session"
        finally:
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature(stripe_config) -> None:
    """POST /billing/webhook returns 400 for invalid signature."""
    with patch(
        "src.api.billing.stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("Invalid", "sig"),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/billing/webhook",
                content=b'{"type":"checkout.session.completed","data":{}}',
                headers={"stripe-signature": "invalid"},
            )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_checkout_session_completed_updates_tier(stripe_config) -> None:
    """checkout.session.completed webhook calls execute to update account_tiers to pro."""
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": TEST_USER_ID,
                "customer": "cus_test123",
            }
        },
    }

    execute_calls = []

    async def capture_execute(query, *args):
        execute_calls.append((query, args))

    with (
        patch(
            "src.api.billing.stripe.Webhook.construct_event",
            return_value=mock_event,
        ),
        patch("src.api.billing.execute", side_effect=capture_execute),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/billing/webhook",
                content=b'{"type":"checkout.session.completed"}',
                headers={"stripe-signature": "t=1,v1=xxx"},
            )
    assert response.status_code == 200
    assert len(execute_calls) >= 1
    # Verify we attempted to upsert account_tiers with pro tier
    upsert_calls = [
        c for c in execute_calls if "pro" in c[0] and "account_tiers" in c[0]
    ]
    assert len(upsert_calls) == 1
    assert TEST_USER_ID in str(upsert_calls[0][1])
    assert "cus_test123" in str(upsert_calls[0][1])
