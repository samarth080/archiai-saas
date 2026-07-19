import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import CheckoutPage from './index'

function renderCheckout(query = '?plan=pro&cycle=monthly') {
  return render(
    <MemoryRouter initialEntries={[`/checkout${query}`]}>
      <Routes>
        <Route path="/checkout" element={<CheckoutPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Checkout page', () => {
  it('shows the selected plan, totals, and disabled placeholder card fields', () => {
    renderCheckout('?plan=team&cycle=monthly')

    expect(screen.getByRole('heading', { name: 'Checkout' })).toBeInTheDocument()
    expect(screen.getByText('Team')).toBeInTheDocument()
    expect(screen.getByText('$79/mo')).toBeInTheDocument()
    expect(screen.getAllByText(/demo checkout flow/i).length).toBeGreaterThan(0)

    const cardField = screen.getByLabelText('Card number (disabled placeholder)')
    expect(cardField).toBeDisabled()

    // No editor chrome on checkout.
    expect(screen.queryByRole('tab', { name: '2D Plan' })).not.toBeInTheDocument()
  })

  it('falls back to the Pro plan when the query has no valid plan', () => {
    renderCheckout('')
    expect(screen.getByRole('button', { name: /Subscribe to Pro/ })).toBeInTheDocument()
  })

  it('completes the demo checkout without touching real payment state', async () => {
    renderCheckout('?plan=pro&cycle=annual')
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: /Subscribe to Pro/ }))

    expect(
      await screen.findByRole('heading', { name: 'Demo checkout complete' }, { timeout: 3000 }),
    ).toBeInTheDocument()
    expect(screen.getByText(/^DEMO-/)).toBeInTheDocument()
    expect(screen.getByText(/no payment was made/i)).toBeInTheDocument()
  })
})
