# Driver Payment System - Stripe Connect (Canada)

Documentation for implementing driver payouts using Stripe Connect in Canada.

## Prerequisites (Required for ALL Payout Options)

No matter which payout method you choose (manual, batch, or API), these steps are **always required**:

| Step | Why |
|------|-----|
| **1. Stripe Hosted Onboarding** | Driver must connect bank account, verify identity |
| **2. Database Link** | You need `stripe_account_id` to know WHO to pay |

```
Driver signs up → Stripe Onboarding → stripe_account_id saved → THEN payouts possible
```

### What Changes by Payout Option

| Component | Manual Dashboard | API System |
|-----------|------------------|------------|
| Stripe Hosted Onboarding | Required | Required |
| Database Link (`stripe_account_id`) | Required | Required |
| Webhook Setup | Optional | Required |
| Backend payout code | Not needed | Required |

### Minimum Setup (All Options)

1. Create Stripe Connect account (Dashboard)
2. Implement driver onboarding flow:
   - Create connected account (API)
   - Redirect to Stripe hosted form
   - Save `stripe_account_id` to database
3. Choose payout method later

The payout method is independent - you can start with manual Dashboard payouts and switch to API later without changing the onboarding flow.

---

## Overview

```
Platform receives delivery payment
    ↓
Split between platform fee + driver earnings
    ↓
Driver receives funds to their connected account
    ↓
Stripe pays out to driver's Canadian bank (2 business days)
```

---

## Required Driver Information (Canada)

### 1. Identity Verification
- Full legal name
- Date of birth
- **SIN (Social Insurance Number)** - last 4 digits or full
- Government ID (driver's license or passport)

### 2. Address
- Street address
- City
- Province
- Postal code (e.g., M5V 1A1)

### 3. Bank Account (for payouts)
- **Institution number** (3 digits)
- **Transit number** (5 digits)
- **Account number** (7-12 digits)
- Account holder name

Example: `003` (institution) + `12345` (transit) + `1234567` (account)

### 4. Contact
- Email address
- Phone number

---

## Canada-Specific Notes

| Item | Details |
|------|---------|
| **Currency** | CAD payouts to Canadian banks |
| **Payout timing** | 2 business days (standard) |
| **Instant payouts** | Available for eligible accounts |
| **Tax forms** | T4A may be required for >$500/year |
| **Minimum payout** | $0.50 CAD |

---

## Environment Variables

```bash
# .env

# Stripe API Keys (from dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx      # Backend API calls
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx # Frontend (optional)

# Webhook Secret (from dashboard.stripe.com/webhooks)
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Optional - for Connect OAuth
STRIPE_CLIENT_ID=ca_xxxxxxxxxxxxxxxxxxxxx
```

### Where to Find Each Key

| Key | Location in Stripe Dashboard |
|-----|------------------------------|
| **Secret Key** | Developers → API Keys → Secret key |
| **Publishable Key** | Developers → API Keys → Publishable key |
| **Webhook Secret** | Developers → Webhooks → Select endpoint → Signing secret |
| **Client ID** | Settings → Connect → Platform settings |

### Test vs Live Keys

```bash
# Test mode (use during development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Live mode (production)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Minimal Setup for Express Connect

```bash
# Minimum required
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
```

---

## Stripe Hosted Onboarding Flow

### How It Works

```
Your App                         Stripe
   │                               │
   ├─1. Create Connect Account ───→│
   │←── account.id ───────────────┤
   │                               │
   ├─2. Create Account Link ──────→│
   │←── onboarding URL ───────────┤
   │                               │
   ├─3. Redirect driver to URL ───→│
   │                               │
   │    [Driver fills Stripe form] │
   │                               │
   │←─4. Driver returns to your app┤
   │                               │
   ├─5. Check account status ─────→│
   │←── verification status ──────┤
```

### What Driver Sees (Stripe's Form)

Stripe automatically collects:

| Screen | Information Collected |
|--------|----------------------|
| **Personal info** | Name, DOB, address, phone |
| **Identity** | SIN (last 4), ID upload if needed |
| **Bank account** | Institution/transit/account numbers |
| **Review** | Terms acceptance |

The form is:
- Mobile-friendly
- Localized (English/French for Canada)
- Handles validation & errors
- PCI/security compliant

---

## Implementation

### Step 1: Create Connected Account (when driver signs up)

```javascript
const account = await stripe.accounts.create({
  type: 'express',
  country: 'CA',
  email: 'driver@email.com',
  capabilities: {
    transfers: { requested: true },
  },
  business_type: 'individual',
  metadata: {
    driver_id: 'your_internal_driver_id'
  }
});

// Save account.id to your database
// e.g., driver.stripe_account_id = account.id
```

### Step 2: Generate Onboarding Link

```javascript
const accountLink = await stripe.accountLinks.create({
  account: 'acct_xxxxx',  // from step 1
  refresh_url: 'https://yourapp.com/driver/stripe/refresh',
  return_url: 'https://yourapp.com/driver/stripe/complete',
  type: 'account_onboarding',
});

// Redirect driver to accountLink.url
// Link expires in ~5 minutes
```

### Step 3: Handle Return URLs

```javascript
// return_url - Driver completed onboarding
app.get('/driver/stripe/complete', async (req, res) => {
  const account = await stripe.accounts.retrieve('acct_xxxxx');

  if (account.details_submitted) {
    // Driver finished filling form
    // Check if fully verified
    if (account.charges_enabled && account.payouts_enabled) {
      // ✅ Ready to receive payouts
    } else {
      // ⏳ Stripe still verifying (usually instant, sometimes 1-2 days)
    }
  }
});

// refresh_url - Link expired or error, generate new link
app.get('/driver/stripe/refresh', async (req, res) => {
  const newLink = await stripe.accountLinks.create({
    account: 'acct_xxxxx',
    refresh_url: 'https://yourapp.com/driver/stripe/refresh',
    return_url: 'https://yourapp.com/driver/stripe/complete',
    type: 'account_onboarding',
  });
  res.redirect(newLink.url);
});
```

### Step 4: Check Account Status

```javascript
const account = await stripe.accounts.retrieve('acct_xxxxx');

// Key fields to check:
account.details_submitted    // Driver finished form
account.charges_enabled      // Can receive payments
account.payouts_enabled      // Can receive payouts ← most important
account.requirements         // Any pending/missing info
```

---

## Webhooks

### Setup

1. Go to **Developers → Webhooks** in Stripe Dashboard
2. Add endpoint: `https://yourapi.com/webhooks/stripe`
3. Select events:
   - `account.updated`
   - `transfer.created`
   - `payout.paid`
   - `payout.failed`
4. Copy the signing secret → `STRIPE_WEBHOOK_SECRET`

### Local Testing

Use [Stripe CLI](https://stripe.com/docs/stripe-cli):

```bash
stripe listen --forward-to localhost:3000/webhooks/stripe
```

### Webhook Handler

```javascript
app.post('/webhooks/stripe', (req, res) => {
  const event = req.body;

  if (event.type === 'account.updated') {
    const account = event.data.object;

    if (account.payouts_enabled) {
      // Update driver status: ready for payouts
    }

    if (account.requirements.currently_due.length > 0) {
      // Driver needs to provide more info
    }
  }

  res.sendStatus(200);
});
```

---

## Making Payouts to Drivers

```javascript
// Transfer earnings to driver's connected account
const transfer = await stripe.transfers.create({
  amount: 2500,  // $25.00 CAD (in cents)
  currency: 'cad',
  destination: 'acct_xxxxx',  // driver's account
  metadata: {
    delivery_ids: 'del_123,del_456'
  }
});

// Stripe automatically pays out to their bank (2 business days)
```

---

## Backend Usage Examples

### Node.js

```javascript
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
```

### Python

```python
import stripe
import os

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
```

### PHP

```php
\Stripe\Stripe::setApiKey($_ENV['STRIPE_SECRET_KEY']);
```

---

## Summary

| Aspect | Stripe Hosted (Express) |
|--------|-------------------------|
| **Your work** | Create account + redirect |
| **Stripe handles** | Form UI, validation, KYC, compliance, bank verification |
| **Security** | Stripe stores all sensitive data |
| **Maintenance** | Stripe updates for regulation changes |
| **Cost** | Free for onboarding, fees on transfers |

This is the recommended approach - you never touch sensitive bank/SIN data directly.

---

## Database Design - App-Stripe Linking

### Core Concept

Store the Stripe `account_id` in your driver table:

```
Your Database                    Stripe
┌─────────────────┐             ┌─────────────────┐
│ drivers         │             │ Connect Account │
├─────────────────┤             ├─────────────────┤
│ id              │─────────────│                 │
│ name            │             │ acct_xxxxx      │
│ email           │             │ (stores bank,   │
│ stripe_account_id ──────────→│  SIN, identity) │
│ stripe_status   │             │                 │
└─────────────────┘             └─────────────────┘
```

### Database Table Design

```sql
-- Add to existing drivers table
ALTER TABLE drivers ADD COLUMN stripe_account_id VARCHAR(255) NULL;
ALTER TABLE drivers ADD COLUMN stripe_status ENUM('pending', 'onboarding', 'verified', 'restricted') DEFAULT 'pending';
ALTER TABLE drivers ADD COLUMN stripe_payouts_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE drivers ADD COLUMN stripe_onboarding_completed_at TIMESTAMP NULL;

-- Or create new table for payment info
CREATE TABLE driver_payment_accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    stripe_account_id VARCHAR(255) UNIQUE,
    status ENUM('pending', 'onboarding', 'verified', 'restricted') DEFAULT 'pending',
    payouts_enabled BOOLEAN DEFAULT FALSE,
    details_submitted BOOLEAN DEFAULT FALSE,
    onboarding_completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);
```

### Key Fields Explained

| Field | Purpose |
|-------|---------|
| `stripe_account_id` | Links to Stripe (e.g., `acct_1234xxxxx`) |
| `status` | Track onboarding progress |
| `payouts_enabled` | Can receive money (from webhook) |
| `details_submitted` | Driver completed Stripe form |

### Workflow with Database

```javascript
// 1. Driver signs up - create Stripe account
const account = await stripe.accounts.create({
  type: 'express',
  country: 'CA',
  email: driver.email,
});

// Save to database
await db.query(
  'UPDATE drivers SET stripe_account_id = ?, stripe_status = ? WHERE id = ?',
  [account.id, 'onboarding', driver.id]
);

// 2. Webhook updates status
app.post('/webhooks/stripe', async (req, res) => {
  const event = req.body;

  if (event.type === 'account.updated') {
    const account = event.data.object;

    await db.query(`
      UPDATE drivers
      SET stripe_status = ?,
          stripe_payouts_enabled = ?
      WHERE stripe_account_id = ?`,
      [
        account.payouts_enabled ? 'verified' : 'onboarding',
        account.payouts_enabled,
        account.id
      ]
    );
  }
});

// 3. Pay driver - lookup by driver_id
async function payDriver(driverId, amountCents) {
  const driver = await db.query(
    'SELECT stripe_account_id FROM drivers WHERE id = ?',
    [driverId]
  );

  if (!driver.stripe_account_id) {
    throw new Error('Driver not connected to Stripe');
  }

  return stripe.transfers.create({
    amount: amountCents,
    currency: 'cad',
    destination: driver.stripe_account_id,
  });
}
```

### Track Payouts (Optional)

```sql
CREATE TABLE driver_payouts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    stripe_transfer_id VARCHAR(255) UNIQUE,
    amount_cents INT NOT NULL,
    currency VARCHAR(3) DEFAULT 'cad',
    status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    delivery_ids JSON,  -- track which deliveries this payout covers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);
```

### What to Store Where

| What to Store | Where |
|---------------|-------|
| `stripe_account_id` | Your database (drivers table) |
| Bank details, SIN, identity | Stripe (never in your DB) |
| Payout status | Your database (synced via webhook) |
| Transfer history | Your database + Stripe |

You only store the **link** (`stripe_account_id`) - Stripe holds all the sensitive financial data.

---

## Payout Options

### Option 1: Manual Payout via Stripe Dashboard

You can log into Stripe Dashboard and pay drivers manually:

```
Stripe Dashboard → Connect → Accounts → Select Driver → Create Transfer
```

#### Steps:
1. Go to **dashboard.stripe.com**
2. Navigate to **Connect → Accounts**
3. Find the driver's connected account
4. Click **Create transfer**
5. Enter amount and confirm

#### Pros/Cons

| Pros | Cons |
|------|------|
| No coding needed | Manual work for each payout |
| Visual verification | Time-consuming with many drivers |
| Good for low volume | Human error risk |
| Quick to start | No automation |

---

### Option 2: Separate Payment System (API)

Another backend system calls Stripe API to process payouts:

```
Delivery App                    Payment System                 Stripe
    │                               │                            │
    ├── Driver completes delivery ─→│                            │
    │                               ├── Calculate earnings       │
    │                               ├── stripe.transfers.create ─→│
    │                               │←── transfer confirmed ─────┤
    │←── Update delivery status ────┤                            │
```

#### What Payment System Needs:

```bash
# Same Stripe keys
STRIPE_SECRET_KEY=sk_live_xxxxx
```

```javascript
// Payment system just needs driver's stripe_account_id
const transfer = await stripe.transfers.create({
  amount: 2500,
  currency: 'cad',
  destination: 'acct_xxxxx',  // from your database
});
```

---

### Option 3: Hybrid (Recommended for Starting)

| Volume | Approach |
|--------|----------|
| **< 50 payouts/week** | Manual via Dashboard |
| **50-200 payouts/week** | Batch via Dashboard CSV upload |
| **> 200 payouts/week** | Automated API system |

#### Dashboard Batch Payouts

Stripe supports bulk transfers via CSV:
1. Export driver earnings from your system
2. Upload to Stripe Dashboard
3. Review and confirm

---

### Payout Method Summary

| Method | Best For |
|--------|----------|
| **Dashboard manual** | Starting out, low volume, testing |
| **Dashboard batch** | Medium volume, weekly payouts |
| **API (separate system)** | High volume, real-time payouts |

You can start with Dashboard manual payouts and build the automated system later when volume grows.

---

## Useful Links

- [Stripe Connect Documentation](https://stripe.com/docs/connect)
- [Express Account Onboarding](https://stripe.com/docs/connect/express-accounts)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Stripe Dashboard](https://dashboard.stripe.com)
- [Connect Account Types](https://stripe.com/docs/connect/accounts)
