import { describe, expect, it } from 'vitest'

import { getApiErrorMessage } from './apiError'

describe('getApiErrorMessage', () => {
  it('returns structured backend errors', () => {
    const message = getApiErrorMessage(
      {
        response: {
          data: {
            error: 'Email already registered',
            code: 'CONFLICT',
            status: 409,
          },
        },
      },
      'Fallback error',
    )

    expect(message).toBe('Email already registered')
  })

  it('formats validation details', () => {
    const message = getApiErrorMessage(
      {
        response: {
          data: {
            detail: [{ loc: ['body', 'password'], msg: 'Password must be at least 8 characters' }],
          },
        },
      },
      'Fallback error',
    )

    expect(message).toBe('password: Password must be at least 8 characters')
  })

  it('returns a clear server unavailable message for network errors', () => {
    const message = getApiErrorMessage({ request: {} }, 'Fallback error')

    expect(message).toBe('Server unavailable. Check that the backend is running on http://localhost:8000.')
  })
})
