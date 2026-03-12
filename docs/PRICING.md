---
title: Pricing
description: Start free. Scale when ready.
---

# Flexible Plans

Choose the plan that fits your needs. Start free, upgrade when ready.

<CardGroup cols={2}>
  <Card title="Free" icon="gift">
    Perfect for testing and personal projects
    
    **$0/month forever**
    
    - 100 MB storage
    - 500 files
    - 1,000 requests/day
    - 1 workspace
    - Community support
    
    <Button href="https://bossa.mintlify.app/GETTING_STARTED">Get Started Free</Button>
  </Card>
  
  <Card title="Pro" icon="rocket">
    For production agents and multiple projects
    
    **$29/month**
    
    - 10 GB storage (100x more)
    - 200,000 files (400x more)
    - 100,000 requests/day (100x more)
    - Unlimited workspaces
    - Email support (24hr response)
    
    <Button href="#">Upgrade to Pro</Button>
  </Card>
</CardGroup>

---

## Which Tier is Right for You?

### Choose Free if you're:
- Learning Bossa and testing features
- Building side projects or prototypes
- Using a single agent with low usage
- Just getting started

### Choose Pro if you're:
- Running agents in production
- Managing multiple projects/workspaces
- Building for clients or teams
- Need more storage or requests

---

## Frequently Asked Questions

<AccordionGroup>
  <Accordion title="What counts as an API request?">
    Each operation (ls, read, write, grep, glob, edit, delete) counts as 1 request. 
    
    Example: `bossa files write /note.md "text"` = 1 request
  </Accordion>
  
  <Accordion title="What happens if I exceed my limits?">
    You'll receive a 402 Payment Required error with upgrade instructions. No surprise charges.
    
    Check your usage anytime: `bossa usage`
  </Accordion>
  
  <Accordion title="Can I change tiers anytime?">
    Yes! Upgrade instantly with `bossa billing upgrade`. Downgrades take effect at the next billing cycle.
  </Accordion>
  
  <Accordion title="Is there a free trial for Pro?">
    The free tier IS your trial. Use Bossa free forever, or upgrade when you need more capacity.
  </Accordion>
  
  <Accordion title="How do workspaces work on Pro?">
    Pro includes unlimited workspaces. Storage, files, and requests are shared across all your workspaces.
    
    Example: If you have 5 workspaces, they all share the 10 GB storage pool.
  </Accordion>
  
  <Accordion title="Can I self-host?">
    Yes! Bossa is open source (MIT). Self-hosting docs: [Self-Hosting Guide](/SELF_HOSTING)
    
    Pro tier benefits (support, hosted reliability) only apply to the managed service.
  </Accordion>
</AccordionGroup>

---

## Usage Tracking

**Check your current usage:**
```bash
bossa usage
```

**Upgrade to Pro:**
```bash
bossa billing upgrade
```

**Manage your subscription:**
```bash
bossa billing manage
```

---

## Technical Details

### Free Tier Limits
| Metric | Limit | Behavior When Exceeded |
|--------|-------|----------------------|
| Storage | 100 MB | Write operations return 402 |
| Files | 500 | Write operations return 402 |
| Requests | 1,000/day | All operations return 402 until next day (UTC) |
| Workspaces | 1 | `bossa workspaces create` returns 402 |

### Pro Tier Limits
| Metric | Limit | Behavior When Exceeded |
|--------|-------|----------------------|
| Storage | 10 GB | Write operations return 402 |
| Files | 200,000 | Write operations return 402 |
| Requests | 100,000/day | All operations return 402 until next day (UTC) |
| Workspaces | Unlimited | Shared quota across all workspaces |

### What Counts Toward Limits?
- **Storage**: Total size of all files in your workspace(s)
- **Files**: Number of files stored
- **Requests**: Each CLI/API/MCP operation (ls, read, write, grep, glob, edit, delete)

---

## Need More?

Building something bigger? Contact us about enterprise plans:
- Custom storage/request limits
- Team collaboration features
- SSO/SAML
- Priority support (24hr response)
- Custom SLAs

📧 Email: vinny.purgato@gmail.com

---

## Self-Hosting

When self-hosting, you control limits via the `account_tiers` table and `OWNER_USER_IDS` config. See [Self-Hosting](SELF_HOSTING) for details.
