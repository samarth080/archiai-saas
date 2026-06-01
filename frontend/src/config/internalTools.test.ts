import { afterEach, describe, expect, it, vi } from 'vitest'

import { isInternalDataPipelineEnabled } from './internalTools'

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('isInternalDataPipelineEnabled', () => {
  it('is disabled by default', () => {
    vi.stubEnv('VITE_SHOW_DEV_TOOLS', '')

    expect(isInternalDataPipelineEnabled()).toBe(false)
  })

  it('requires an explicit true value', () => {
    vi.stubEnv('VITE_SHOW_DEV_TOOLS', 'true')

    expect(isInternalDataPipelineEnabled()).toBe(true)
  })
})
