type ValidationDetail = {
  loc?: Array<string | number>
  msg?: string
}

type ApiErrorPayload = {
  error?: string
  detail?: string | ValidationDetail[]
  message?: string
}

type ApiErrorLike = {
  response?: {
    data?: ApiErrorPayload
  }
  request?: unknown
  message?: string
}

function formatValidationDetails(details: ValidationDetail[]) {
  return details
    .map((detail) => {
      const field = detail.loc?.filter((part) => part !== 'body').join('.')
      return field ? `${field}: ${detail.msg}` : detail.msg
    })
    .filter(Boolean)
    .join('; ')
}

export function getApiErrorMessage(error: unknown, fallback: string) {
  const apiError = error as ApiErrorLike
  const data = apiError.response?.data

  if (typeof data?.error === 'string' && data.error.trim()) {
    return data.error
  }

  if (typeof data?.detail === 'string' && data.detail.trim()) {
    return data.detail
  }

  if (Array.isArray(data?.detail)) {
    const validationMessage = formatValidationDetails(data.detail)
    if (validationMessage) {
      return validationMessage
    }
  }

  if (typeof data?.message === 'string' && data.message.trim()) {
    return data.message
  }

  if (apiError.request && !apiError.response) {
    return 'Server unavailable. Check that the backend is running on http://localhost:8000.'
  }

  return fallback
}
