import { describe, expect, it } from 'vitest'

import { shouldRedirectOnUnauthorized } from './api'

describe('shouldRedirectOnUnauthorized', () => {
  it('keeps invalid login errors on the form', () => {
    expect(
      shouldRedirectOnUnauthorized({
        response: { status: 401 },
        config: { url: '/api/auth/login' },
      }),
    ).toBe(false)
  })

  it('redirects expired protected requests to login', () => {
    expect(
      shouldRedirectOnUnauthorized({
        response: { status: 401 },
        config: { url: '/api/projects' },
      }),
    ).toBe(true)
  })
})
