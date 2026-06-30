interface PlaceholderThumbnailProps {
  seed: string
}

// Small decorative palette for the placeholder's "room blocks" — these are
// purely presentational accents, not part of the single brand-accent system,
// so reusing Tailwind's default palette here is intentional.
const BLOCK_COLORS = ['bg-brand-200', 'bg-sky-200', 'bg-emerald-200', 'bg-amber-200', 'bg-rose-200']

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

// Deterministic PRNG (mulberry32) seeded from the hash above — never
// Math.random(), so the same project id always renders the same pattern
// with no flicker across re-renders or re-fetches.
function mulberry32(seed: number) {
  let a = seed
  return function next() {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * A decorative plan-style placeholder shown for projects without a saved
 * thumbnail: a light grid, a dashed "plot boundary", and a handful of
 * colored "room blocks" — all derived deterministically from the project id
 * alone (no room/layout data required, since most projects won't have any).
 */
export function PlaceholderThumbnail({ seed }: PlaceholderThumbnailProps) {
  const rand = mulberry32(hashString(seed))
  const inset = 8 + rand() * 8
  const blockCount = 3 + Math.floor(rand() * 3)
  const blocks = Array.from({ length: blockCount }, (_, i) => {
    const w = 18 + rand() * 22
    const h = 18 + rand() * 22
    const left = inset + 4 + rand() * Math.max(1, 100 - 2 * inset - w - 4)
    const top = inset + 4 + rand() * Math.max(1, 100 - 2 * inset - h - 4)
    const color = BLOCK_COLORS[Math.floor(rand() * BLOCK_COLORS.length)]
    return { key: i, w, h, left, top, color }
  })

  return (
    <div
      className="relative h-36 w-full overflow-hidden bg-surface"
      style={{
        backgroundImage:
          'linear-gradient(rgba(38,34,47,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(38,34,47,0.05) 1px, transparent 1px)',
        backgroundSize: '12px 12px',
      }}
    >
      <div
        className="absolute rounded-sm border border-dashed border-ink/20"
        style={{ left: `${inset}%`, top: `${inset}%`, right: `${inset}%`, bottom: `${inset}%` }}
      />
      {blocks.map((block) => (
        <div
          key={block.key}
          className={`absolute rounded-sm opacity-90 ${block.color}`}
          style={{
            left: `${block.left}%`,
            top: `${block.top}%`,
            width: `${block.w}%`,
            height: `${block.h}%`,
          }}
        />
      ))}
    </div>
  )
}
