import { describe, expect, it } from 'vitest'

import { placeholderPaymentService } from './placeholderPayment.service'

describe('placeholderPaymentService', () => {
  it('resolves a demo-only result for a purchasable plan', async () => {
    const result = await placeholderPaymentService.startCheckout('pro', 'annual')

    expect(result.status).toBe('demo_success')
    expect(result.planId).toBe('pro')
    expect(result.billingCycle).toBe('annual')
    expect(result.reference).toMatch(/^DEMO-/)
    expect(result.message).toContain('demo checkout')
    expect(result.message).toContain('no payment was made')
  })

  it('rejects unknown plans', async () => {
    await expect(placeholderPaymentService.startCheckout('gold', 'monthly')).rejects.toThrow(
      'Unknown plan: gold',
    )
  })

  it('rejects enterprise (sales-led) plans', async () => {
    await expect(
      placeholderPaymentService.startCheckout('enterprise', 'monthly'),
    ).rejects.toThrow(/sales/)
  })
})
