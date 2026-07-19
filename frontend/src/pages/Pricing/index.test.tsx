import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import PricingPage from './index'

function LocationProbe() {
  const location = useLocation()
  return <div>at:{location.pathname + location.search}</div>
}

function renderPricing() {
  return render(
    <MemoryRouter initialEntries={['/pricing']}>
      <Routes>
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/checkout" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Pricing page', () => {
  it('renders all four plans with the demo-payment note and no editor chrome', () => {
    renderPricing()

    expect(screen.getByRole('heading', { name: 'Plans & Pricing' })).toBeInTheDocument()
    for (const plan of ['Starter', 'Pro', 'Team', 'Enterprise']) {
      expect(screen.getByRole('heading', { name: plan })).toBeInTheDocument()
    }
    expect(screen.getByText(/demo checkout flow/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Select' })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: '2D Plan' })).not.toBeInTheDocument()
  })

  it('switches prices between monthly and annual billing', async () => {
    renderPricing()
    const user = userEvent.setup()

    expect(screen.getByText('$29/mo')).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: /annual/i }))
    expect(screen.getByText('$290/yr')).toBeInTheDocument()
    expect(screen.queryByText('$29/mo')).not.toBeInTheDocument()
  })

  it('sends a purchasable plan to checkout with plan and cycle params', async () => {
    renderPricing()
    const user = userEvent.setup()

    await user.click(screen.getByRole('tab', { name: /annual/i }))
    await user.click(screen.getByRole('button', { name: 'Start Pro trial' }))

    expect(screen.getByText('at:/checkout?plan=pro&cycle=annual')).toBeInTheDocument()
  })

  it('renders the comparison table', () => {
    renderPricing()

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Team workspaces & roles')).toBeInTheDocument()
  })
})
