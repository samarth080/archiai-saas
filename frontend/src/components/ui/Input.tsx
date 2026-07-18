import { forwardRef, InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={inputId} className="text-sm font-medium text-ink/80">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          {...props}
          className={`rounded-lg border bg-graphite-700 px-3 py-2 text-sm text-ink placeholder:text-muted-light focus:outline-none focus:ring-2 focus:ring-ink/30 ${
            error ? 'border-danger' : 'border-ink/15'
          }`}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
