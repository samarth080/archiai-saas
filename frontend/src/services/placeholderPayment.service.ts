import { planById, type BillingCycle } from '../constants/plans'

/**
 * DEMO-ONLY checkout adapter. The real payment gateway is not integrated
 * yet, so this service exists to keep the checkout UI flow testable while
 * guaranteeing that nothing real can happen:
 *
 * - no network calls, no card data read or stored, no persistence
 * - never marks a user as subscribed anywhere (no store/localStorage writes)
 * - resolves with an explicit `demo_success` status the UI must label as demo
 *
 * Replacing it later: swap `startCheckout` for a call that creates a real
 * order (e.g. `POST /api/billing/orders` for Razorpay, or Stripe Checkout)
 * and keep the same function signature so the pages don't change.
 */

export interface DemoCheckoutResult {
  status: 'demo_success'
  reference: string
  planId: string
  billingCycle: BillingCycle
  message: string
}

const DEMO_DELAY_MS = 700

export const placeholderPaymentService = {
  async startCheckout(planId: string, billingCycle: BillingCycle): Promise<DemoCheckoutResult> {
    const plan = planById(planId)
    if (!plan) {
      throw new Error(`Unknown plan: ${planId}`)
    }
    if (plan.priceMonthly === null) {
      throw new Error('Enterprise plans are handled by sales, not self-serve checkout.')
    }
    await new Promise((resolve) => setTimeout(resolve, DEMO_DELAY_MS))
    return {
      status: 'demo_success',
      reference: `DEMO-${Date.now().toString(36).toUpperCase()}`,
      planId,
      billingCycle,
      message:
        'This is a demo checkout flow. Payment gateway integration is pending — no payment was made and no subscription was activated.',
    }
  },
}
