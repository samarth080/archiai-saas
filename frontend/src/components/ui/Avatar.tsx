// Deterministic avatar color from a hash of the user's name/email, so the
// same person always gets the same color (no randomness, no extra data).
const AVATAR_COLORS = ['#7A6CD6', '#3FA39B', '#E08A6B', '#C77DBB', '#5B8DD9']

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

interface AvatarProps {
  name: string
  size?: number
}

export function Avatar({ name, size = 8 }: AvatarProps) {
  const initial = name.trim().charAt(0).toUpperCase() || '?'
  const color = AVATAR_COLORS[hashString(name) % AVATAR_COLORS.length]
  return (
    <span
      aria-hidden="true"
      className="flex flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
      style={{ backgroundColor: color, height: `${size * 0.25}rem`, width: `${size * 0.25}rem` }}
    >
      {initial}
    </span>
  )
}
