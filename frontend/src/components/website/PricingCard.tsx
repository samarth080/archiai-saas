import { formatPlanPrice, type BillingCycle, type PlanDefinition } from '../../constants/plans'

interface PricingCardProps {
  plan: PlanDefinition
  cycle: BillingCycle
  compact?: boolean
  onSelect: (plan: PlanDefinition) => void
}

export function PricingCard({ plan, cycle, compact = false, onSelect }: PricingCardProps) {
  const price = formatPlanPrice(plan, cycle)

  return (
    <div
      className={`relative flex flex-col rounded-2xl border p-5 ${
        plan.highlighted
          ? 'border-ink/40 bg-graphite-750 shadow-[0_18px_50px_rgba(0,0,0,0.35)]'
          : 'border-ink/10 bg-graphite-800/80'
      }`}
    >
      {plan.highlighted && (
        <span className="absolute -top-2.5 left-5 rounded-full bg-ink px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-graphite-900">
          Most popular
        </span>
      )}
      <h3 className="text-sm font-semibold text-ink">{plan.name}</h3>
      <p className="mt-0.5 text-xs text-muted-light">{plan.tagline}</p>
      <p className="mt-3 text-2xl font-bold text-ink">
        {price}
        {price !== 'Custom' && price !== 'Free' && cycle === 'annual' && (
          <span className="ml-1.5 align-middle text-[11px] font-medium text-ok">2 months free</span>
        )}
      </p>
      <ul className={`mt-4 flex flex-col gap-1.5 ${compact ? '' : 'flex-1'}`}>
        {(compact ? plan.features.slice(0, 4) : plan.features).map((feature) => (
          <li key={feature} className="flex items-start gap-2 text-[13px] text-muted">
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="mt-0.5 shrink-0 text-ink/60"
              aria-hidden="true"
            >
              <path d="M20 6L9 17l-5-5" />
            </svg>
            {feature}
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => onSelect(plan)}
        className={`mt-5 w-full rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
          plan.highlighted
            ? 'bg-ink text-graphite-900 hover:bg-graphite-100'
            : 'border border-ink/15 text-ink hover:bg-ink/5'
        }`}
      >
        {plan.cta}
      </button>
    </div>
  )
}
