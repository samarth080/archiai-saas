# SaaS Hardening & Monetization

Covers the security lifecycle (Sprint 17 Phase 0) and the billing/entitlement
foundation (Phase 3).

## Authentication lifecycle (Phase 0)

- **Access tokens**: HS256 JWT, **45-minute** expiry, carrying `sub`, `jti`,
  `iat`, and a `type: "access"` claim. (Was 7 days with no revocation.)
- **Refresh tokens**: 30-day JWT with `type: "refresh"`; only a **SHA-256 hash**
  is stored (`refresh_tokens` table) so a DB read cannot mint a session.
- **`POST /api/auth/refresh`** rotates: it revokes the presented token and
  issues a fresh access+refresh pair. Reuse of a rotated token is refused.
- **`/logout`** revokes the presented refresh token.
- Access-protected routes reject refresh tokens (and vice-versa) via the `type`
  claim.
- **Token storage tradeoff**: tokens currently live in `localStorage`. Pair with
  the short access-token expiry + refresh rotation + CSP (below). Migrating to an
  httpOnly cookie is a future option; whichever is chosen keeps short expiry.

## Perimeter hardening (Phase 0)

- **Scraper is admin-only** (`User.is_admin`): every `/api/scraper/*` route is
  gated; non-admins get 403. Previously any authenticated user could create
  arbitrary-URL sources and trigger server-side fetches.
- **SSRF guard** (`utils/ssrf.py`): every outbound-fetch URL is resolved and
  rejected if it maps to a private/loopback/link-local (incl. `169.254.169.254`
  cloud metadata)/reserved/multicast address (v4+v6, incl. IPv4-mapped IPv6);
  fails closed; re-validated on every redirect hop.
- **Rate limiting** (`utils/rate_limit.py`): per-user-or-IP sliding window on
  login/register/refresh/generate/share/scraper-run/billing; 429 on exceed.
- **Payload caps**: prompt ≤ 2000 chars, layout JSON ≤ 2 MB, request body ≤ 3 MB
  (413/422).
- **Production config**: env-driven `ENV` + `ALLOWED_ORIGINS`; security headers
  (CSP, HSTS, X-Content-Type-Options, Referrer-Policy, X-Frame-Options) in
  production; the app **refuses to boot** in production with a weak/placeholder
  `SECRET_KEY` or a `*` CORS origin.

## Monetization (Phase 3)

Backend-verified; the frontend never decides entitlement.

### Data model (migration 014)

`Plan` (code, price, interval, `limits` JSON), `Subscription` (user, plan,
status, period end), `PaymentOrder` (Razorpay order id, amount, status),
`PaymentEvent` (raw verified webhook, idempotency key), `Entitlement`
(subject → feature override), `UsageCounter` (subject, metric, window, count).

**No card / bank / UPI / PAN data is ever stored** — only Razorpay's opaque ids
and our own bookkeeping (asserted by a test).

### Entitlements & quotas (`entitlement_service`)

Effective limits resolve server-side: active `Subscription` → `Plan` row (or
built-in free/pro defaults) → per-user `Entitlement` overrides. Free tier:
3 projects, 50 generations/month, paid features off. Gates:
`require_within_project_limit` (**402**), `require_feature` (**403** — stubs for
DXF/BIM export, team workspaces, advanced furniture, commercial templates),
`enforce_and_increment_usage` (metered generations). **Admins bypass all gates**
— the manual override / reconciliation escape hatch.

### Razorpay flow (`billing_service`, no SDK)

1. `POST /api/billing/orders` creates a Razorpay order server-side (httpx) and
   records a `PaymentOrder`.
2. The browser completes checkout with the public `key_id`.
3. Razorpay calls `POST /api/billing/webhook`. The handler **verifies the
   `X-Razorpay-Signature`** (stdlib HMAC-SHA256, constant-time), is **idempotent**
   on `X-Razorpay-Event-Id`, and is the **only** place an order is marked paid /
   a subscription activated. Client-reported status is never trusted.

Keys come from env (`RAZORPAY_KEY_ID/KEY_SECRET/WEBHOOK_SECRET`); none committed.
Order creation and the webhook are disabled until configured.

## Deferred (Phase 10)

Password reset, email verification, account lockout/deletion, an admin
dashboard, error-monitoring hooks, analytics, retention policy, and a full
cross-user authz test matrix.
