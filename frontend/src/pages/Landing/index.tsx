import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { WebsiteNavbar } from '../../components/website/WebsiteNavbar'
import { WebsiteFooter } from '../../components/website/WebsiteFooter'
import { EditorPreviewCard } from '../../components/website/EditorPreviewCard'
import { FeatureCard } from '../../components/website/FeatureCard'
import { PricingCard } from '../../components/website/PricingCard'
import { DemoModal } from '../../components/website/DemoModal'
import { PLANS, type PlanDefinition } from '../../constants/plans'

const TRUST_ITEMS = [
  'AI-assisted design',
  'Smart constraints',
  'Built for teams',
  'Cloud-native',
]

const FEATURES = [
  {
    title: 'AI-Powered Design',
    description:
      'Describe the building in plain language — ArchiAI extracts the program and generates an editable, deterministic layout in seconds.',
    icon: (
      <>
        <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4z" />
        <path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z" />
      </>
    ),
  },
  {
    title: 'Built-in Compliance',
    description:
      'Hard geometric validation on every plan: no overlaps, minimum room sizes, and a walkable door graph — checked before you ever see it.',
    icon: (
      <>
        <path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6z" />
        <path d="M9 12l2 2 4-4" />
      </>
    ),
  },
  {
    title: 'Team Collaboration',
    description:
      'Shared workspaces with owner, admin, editor, and viewer roles, plus version history and a full activity trail on every project.',
    icon: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
        <circle cx="17.5" cy="9.5" r="2.5" />
        <path d="M21 19c0-2.5-1.6-4.6-3.8-5.4" />
      </>
    ),
  },
  {
    title: 'Cloud-Native',
    description:
      'Projects, versions, drafts, and share links live in the cloud — open the same layout from anywhere and pick up where you left off.',
    icon: (
      <>
        <path d="M7 18a4.5 4.5 0 1 1 .6-8.96 6 6 0 0 1 11.4 1.7A4 4 0 0 1 18 18z" />
      </>
    ),
  },
]

const SOLUTIONS = [
  {
    title: 'Architecture studios',
    description: 'Concept massing and space programs before committing CAD hours.',
  },
  {
    title: 'Interior & space planners',
    description: 'Zoning, adjacency, and circulation reasoning on real footprints.',
  },
  {
    title: 'Real-estate & developers',
    description: 'Fast, presentable layout options for plots and briefs that change daily.',
  },
]

export default function Landing() {
  const navigate = useNavigate()
  const [demoModal, setDemoModal] = useState<'watch' | 'book' | null>(null)

  const goToPricing = (plan?: PlanDefinition) => {
    navigate(plan ? `/pricing?plan=${plan.id}` : '/pricing')
  }

  return (
    <div className="min-h-screen bg-surface text-ink">
      <WebsiteNavbar onBookDemo={() => setDemoModal('book')} />

      {/* Hero */}
      <section className="mx-auto grid w-full max-w-6xl items-center gap-10 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.05fr_1.2fr] lg:pt-20">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-ink/15 bg-ink/5 px-3 py-1 text-xs font-medium text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-ok" aria-hidden="true" />
            AI-powered architectural design
          </span>
          <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight text-ink sm:text-5xl">
            Design better spaces, faster.
          </h1>
          <p className="mt-4 max-w-lg text-base leading-relaxed text-muted">
            ArchiAI helps architects and designers create, refine, and optimize
            floor plans with AI-powered tools built for real-world projects.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => goToPricing()}
              className="rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-graphite-900 transition-colors hover:bg-graphite-100"
            >
              Start Free Trial
            </button>
            <button
              type="button"
              onClick={() => setDemoModal('watch')}
              className="flex items-center gap-2 rounded-lg border border-ink/15 px-5 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-ink/5"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M8 5v14l11-7z" />
              </svg>
              Watch Demo
            </button>
          </div>
          <p className="mt-4 text-xs text-muted-light">
            Free plan available · No credit card required
          </p>
        </div>

        <EditorPreviewCard />
      </section>

      {/* Trust / value row */}
      <section className="border-y border-ink/5 bg-graphite-850">
        <div className="mx-auto grid w-full max-w-6xl grid-cols-2 gap-4 px-4 py-6 sm:px-6 md:grid-cols-4">
          {TRUST_ITEMS.map((item) => (
            <div key={item} className="flex items-center justify-center gap-2 text-sm font-medium text-muted">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="text-ink/50" aria-hidden="true">
                <path d="M20 6L9 17l-5-5" />
              </svg>
              {item}
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="product" className="mx-auto w-full max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6">
        <h2 className="text-2xl font-bold text-ink">Everything from brief to building</h2>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          One workspace covering the whole early-design loop: generate, edit in 2D
          and 3D, reason about zoning and adjacency, then export and share.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <FeatureCard key={feature.title} {...feature} />
          ))}
        </div>
      </section>

      {/* Solutions */}
      <section id="solutions" className="border-y border-ink/5 bg-graphite-850">
        <div className="mx-auto w-full max-w-6xl scroll-mt-20 px-4 py-14 sm:px-6">
          <h2 className="text-2xl font-bold text-ink">Made for teams that plan space</h2>
          <div className="mt-7 grid gap-4 md:grid-cols-3">
            {SOLUTIONS.map((solution) => (
              <div key={solution.title} className="rounded-2xl border border-ink/10 bg-graphite-800/60 p-5">
                <h3 className="text-sm font-semibold text-ink">{solution.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">{solution.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold text-ink">Simple pricing</h2>
            <p className="mt-2 text-sm text-muted">Start free, upgrade when the work gets real.</p>
          </div>
          <Link to="/pricing" className="text-sm font-semibold text-ink underline-offset-4 hover:underline">
            See full pricing →
          </Link>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PLANS.map((plan) => (
            <PricingCard
              key={plan.id}
              plan={plan}
              cycle="monthly"
              compact
              onSelect={goToPricing}
            />
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="border-t border-ink/5 bg-graphite-850">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-4 px-4 py-14 text-center sm:px-6">
          <h2 className="text-2xl font-bold text-ink">Start designing in minutes</h2>
          <p className="max-w-md text-sm text-muted">
            Type a brief, get a plan, and shape it in the editor — 2D, 3D, zoning,
            and room graph on one canvas.
          </p>
          <div className="mt-2 flex gap-3">
            <button
              type="button"
              onClick={() => goToPricing()}
              className="rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-graphite-900 hover:bg-graphite-100"
            >
              Start Free Trial
            </button>
            <button
              type="button"
              onClick={() => setDemoModal('book')}
              className="rounded-lg border border-ink/15 px-5 py-2.5 text-sm font-semibold text-ink hover:bg-ink/5"
            >
              Book a Demo
            </button>
          </div>
        </div>
      </section>

      <WebsiteFooter />

      <DemoModal
        open={demoModal !== null}
        variant={demoModal ?? 'watch'}
        onClose={() => setDemoModal(null)}
      />
    </div>
  )
}
