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
          className={`border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 ${
            error ? 'border-red-500' : 'border-ink/15'
          }`}
        />
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
