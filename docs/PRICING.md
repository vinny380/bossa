---
title: "Pricing & Limits"
description: "Account tiers, usage limits, and upgrade options."
---


Bossa uses tier-based limits for storage, files, requests, and workspaces. Limits are enforced per account (user).

---

## Tiers

| Tier | Storage | Files | Requests/day | Workspaces |
|------|---------|-------|--------------|------------|
| **Free** | 100 MB | 500 | 1,000 | 1 |
| **Pro** | 10 GB | 200,000 | 100,000 | Unlimited |

**Pro:** Unlimited workspaces—create as many as you need. Your total limits (10 GB storage, 200,000 files, 100K requests/day) apply across all workspaces combined.

---

## What Counts Toward Limits

- **Storage** — Total bytes of file content across all workspaces for your account.
- **Files** — Total number of files across all workspaces.
- **Requests** — API calls per day (REST, MCP, CLI). Each `ls`, `read`, `write`, `grep`, etc. counts as one request.
- **Workspaces** — Free tier allows 1 workspace. Pro and Owner have unlimited workspaces.

---

## When Limits Are Exceeded

- **Storage or files** — Write operations return `402 Payment Required` with a message directing you to [upgrade](https://bossa.mintlify.app/pricing).
- **Requests** — Further API calls return `402` until the next day (UTC).
- **Workspaces** — `bossa workspaces create` returns `402` on Free tier when you already have 1 workspace.

---

## Upgrade

Run `bossa billing upgrade` to open Stripe Checkout. Choose monthly or yearly billing with `--interval month` (default) or `--interval year`.

```bash
bossa billing upgrade
bossa billing upgrade --interval year
```

**Manage subscription:** `bossa billing manage` — opens Stripe Customer Portal to update payment method, view invoices, or cancel.

---

## Check Your Usage

Use the Usage API to see current usage and limits:

```
GET /api/v1/usage
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
  "storage_mb": 12.5,
  "files_count": 42,
  "requests_today": 156,
  "tier": "free",
  "limits": {
    "storage_mb": 100,
    "files": 500,
    "requests_per_day": 1000
  }
}
```

---


---

## Self-Hosting

When self-hosting, you control limits via the `account_tiers` table and `OWNER_USER_IDS` config. See [Self-Hosting](SELF_HOSTING) for details.
