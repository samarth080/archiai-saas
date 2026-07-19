// Pricing catalogue for the marketing pages and the demo checkout flow.
// Static config for now — when the billing backend (Sprint 17+ phase3
// branch) lands, this should be replaced by `GET /api/billing/plans` and
// the ids kept in sync with the backend Plan rows.

export type BillingCycle = 'monthly' | 'annual'

export interface PlanDefinition {
  id: string
  name: string
  tagline: string
  /** Monthly price in USD; null = custom/contact sales. */
  priceMonthly: number | null
  /** Annual price in USD (billed yearly); null = custom/contact sales. */
  priceAnnual: number | null
  features: string[]
  highlighted?: boolean
  cta: string
}

export const PLANS: PlanDefinition[] = [
  {
    id: 'starter',
    name: 'Starter',
    tagline: 'For trying out ArchiAI',
    priceMonthly: 0,
    priceAnnual: 0,
    features: [
      '3 projects',
      '2D floor plan editor',
      'Basic 3D view',
      'Standard room blocks',
      'PNG export',
      'Community support',
    ],
    cta: 'Start free',
  },
  {
    id: 'pro',
    name: 'Pro',
    tagline: 'For professional designers',
    priceMonthly: 29,
    priceAnnual: 290,
    features: [
      'Unlimited projects',
      'Advanced 3D editing',
      'Parametric room blocks',
      'Zoning & room graph views',
      'Version history',
      'PNG + PDF exports',
      'Priority support',
    ],
    highlighted: true,
    cta: 'Start Pro trial',
  },
  {
    id: 'team',
    name: 'Team',
    tagline: 'For studios and firms',
    priceMonthly: 79,
    priceAnnual: 790,
    features: [
      'Everything in Pro',
      'Team workspaces',
      'Role-based access',
      'Shared project libraries',
      'Activity & audit logs',
      '5 seats included',
    ],
    cta: 'Start Team trial',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tagline: 'For large organizations',
    priceMonthly: null,
    priceAnnual: null,
    features: [
      'Custom deployment',
      'SSO & security review',
      'Custom integrations',
      'Dedicated support',
      'Onboarding & training',
    ],
    cta: 'Contact sales',
  },
]

export function planById(planId: string | null | undefined) {
  return PLANS.find((plan) => plan.id === planId) ?? null
}

export function planPrice(plan: PlanDefinition, cycle: BillingCycle) {
  return cycle === 'annual' ? plan.priceAnnual : plan.priceMonthly
}

/** "$29/mo", "$290/yr", "Free", or "Custom". */
export function formatPlanPrice(plan: PlanDefinition, cycle: BillingCycle) {
  const price = planPrice(plan, cycle)
  if (price === null) return 'Custom'
  if (price === 0) return 'Free'
  return `$${price}/${cycle === 'annual' ? 'yr' : 'mo'}`
}
