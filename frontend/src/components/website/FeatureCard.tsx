import type { ReactNode } from 'react'

interface FeatureCardProps {
  icon: ReactNode
  title: string
  description: string
}

export function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="rounded-2xl border border-ink/10 bg-graphite-800/80 p-5 transition-colors hover:border-ink/20">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-ink/10 text-ink">
        <svg
          width="17"
          height="17"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          {icon}
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-1.5 text-sm leading-relaxed text-muted">{description}</p>
    </div>
  )
}
