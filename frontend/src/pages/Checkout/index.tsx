import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { WebsiteNavbar } from '../../components/website/WebsiteNavbar'
import { WebsiteFooter } from '../../components/website/WebsiteFooter'
import { DemoModal } from '../../components/website/DemoModal'
import {
  formatPlanPrice,
  planById,
  planPrice,
  type BillingCycle,
} from '../../constants/plans'
import {
  placeholderPaymentService,
  type DemoCheckoutResult,
} from '../../services/placeholderPayment.service'

function DisabledField({ label, placeholder }: { label: string; placeholder: string }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-muted">{label}</label>
      <input
        type="text"
        disabled
        placeholder={placeholder}
        aria-label={`${label} (disabled placeholder)`}
        className="rounded-lg border border-ink/10 bg-graphite-700/60 px-3 py-2 text-sm text-muted-light placeholder:text-graphite-500"
      />
    </div>
  )
}

export default function CheckoutPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [demoOpen, setDemoOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DemoCheckoutResult | null>(null)

  const cycleParam = searchParams.get('cycle')
  const cycle: BillingCycle = cycleParam === 'annual' ? 'annual' : 'monthly'
  const plan = planById(searchParams.get('plan')) ?? planById('pro')!

  const price = planPrice(plan, cycle) ?? 0
  const priceLabel = formatPlanPrice(plan, cycle)

  const setCycle = (next: BillingCycle) => {
    const params = new URLSearchParams(searchParams)
    params.set('cycle', next)
    params.set('plan', plan.id)
    setSearchParams(params, { replace: true })
    setResult(null)
  }

  const handleSubscribe = async () => {
    setSubmitting(true)
    setError(null)
    try {
      setResult(await placeholderPaymentService.startCheckout(plan.id, cycle))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo checkout failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface text-ink">
      <WebsiteNavbar onBookDemo={() => setDemoOpen(true)} />

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 pb-20 pt-12 sm:px-6">
        <Link to="/pricing" className="text-sm font-medium text-muted hover:text-ink">
          ← Back to pricing
        </Link>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-ink">Checkout</h1>
        <p className="mt-2 rounded-lg border border-warn/30 bg-warn/10 px-4 py-2.5 text-xs text-warn">
          This is a demo checkout flow. Payment gateway integration is pending —
          no card is charged, no data is stored, and no subscription is activated.
        </p>

        {result ? (
          <div className="mt-8 rounded-2xl border border-ok/30 bg-graphite-800 p-6">
            <div className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ok/15 text-ok">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
              </span>
              <h2 className="text-lg font-semibold text-ink">Demo checkout complete</h2>
            </div>
            <p className="mt-3 text-sm text-muted">{result.message}</p>
            <dl className="mt-4 grid gap-2 rounded-lg bg-graphite-850 p-4 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-xs text-muted-light">Reference</dt>
                <dd className="font-mono text-ink">{result.reference}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-light">Plan</dt>
                <dd className="text-ink">{plan.name}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-light">Billing</dt>
                <dd className="capitalize text-ink">{result.billingCycle}</dd>
              </div>
            </dl>
            <div className="mt-5 flex gap-3">
              <Link
                to="/register"
                className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-graphite-900 hover:bg-graphite-100"
              >
                Create your account
              </Link>
              <button
                type="button"
                onClick={() => setResult(null)}
                className="rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-ink/5"
              >
                Back to checkout
              </button>
            </div>
          </div>
        ) : (
          <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            {/* Payment method placeholder */}
            <section className="rounded-2xl border border-ink/10 bg-graphite-800 p-5">
              <h2 className="text-sm font-semibold text-ink">Payment method</h2>
              <p className="mt-1 text-xs text-muted-light">
                Card fields are placeholders and stay disabled until a real
                payment gateway (e.g. Razorpay or Stripe) is connected.
              </p>
              <div className="mt-4 grid gap-3">
                <DisabledField label="Cardholder name" placeholder="Name on card" />
                <DisabledField label="Card number" placeholder="•••• •••• •••• ••••" />
                <div className="grid grid-cols-2 gap-3">
                  <DisabledField label="Expiry" placeholder="MM / YY" />
                  <DisabledField label="CVC" placeholder="•••" />
                </div>
              </div>
            </section>

            {/* Order summary */}
            <section className="flex flex-col rounded-2xl border border-ink/10 bg-graphite-800 p-5">
              <h2 className="text-sm font-semibold text-ink">Order summary</h2>
              <div className="mt-3 flex items-center justify-between rounded-lg bg-graphite-850 px-3 py-2.5">
                <div>
                  <p className="text-sm font-semibold text-ink">{plan.name}</p>
                  <p className="text-xs text-muted-light">{plan.tagline}</p>
                </div>
                <span className="font-mono text-sm text-ink">{priceLabel}</span>
              </div>

              <div className="mt-3 flex items-center gap-1 rounded-lg border border-ink/10 bg-graphite-850 p-1 text-xs">
                {(['monthly', 'annual'] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setCycle(option)}
                    className={`flex-1 rounded-md px-2 py-1.5 font-semibold capitalize ${
                      cycle === option ? 'bg-ink text-graphite-900' : 'text-muted hover:text-ink'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>

              <dl className="mt-4 flex flex-col gap-2 text-sm">
                <div className="flex justify-between text-muted">
                  <dt>Subtotal</dt>
                  <dd className="font-mono">${price}</dd>
                </div>
                <div className="flex justify-between text-muted-light">
                  <dt>Tax (calculated at billing)</dt>
                  <dd className="font-mono">—</dd>
                </div>
                <div className="flex justify-between border-t border-ink/10 pt-2 font-semibold text-ink">
                  <dt>Total</dt>
                  <dd className="font-mono">
                    ${price}
                    <span className="ml-1 text-xs font-normal text-muted-light">
                      /{cycle === 'annual' ? 'yr' : 'mo'}
                    </span>
                  </dd>
                </div>
              </dl>

              {error && <p className="mt-3 text-xs text-danger">{error}</p>}

              <button
                type="button"
                onClick={handleSubscribe}
                disabled={submitting}
                className="mt-5 rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-graphite-900 hover:bg-graphite-100 disabled:opacity-60"
              >
                {submitting ? 'Processing demo…' : `Subscribe to ${plan.name} (demo)`}
              </button>
              <p className="mt-2 text-center text-[11px] text-muted-light">
                Demo only — nothing is charged.
              </p>
            </section>
          </div>
        )}
      </main>

      <WebsiteFooter />
      <DemoModal open={demoOpen} variant="book" onClose={() => setDemoOpen(false)} />
    </div>
  )
}
