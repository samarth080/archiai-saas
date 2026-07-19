import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import Landing from './index'

function renderLanding() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/pricing" element={<div>Pricing page stub</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Landing page', () => {
  it('renders the approved hero without any editor chrome', () => {
    renderLanding()

    expect(
      screen.getByRole('heading', { name: 'Design better spaces, faster.' }),
    ).toBeInTheDocument()
    expect(screen.getByText('AI-powered architectural design')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Start Free Trial' }).length).toBeGreaterThan(0)

    // Website navbar only — no editor tool rail / editor tabs on marketing pages.
    expect(screen.queryByRole('button', { name: 'Select' })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: '2D Plan' })).not.toBeInTheDocument()
  })

  it('shows the feature cards and pricing preview', () => {
    renderLanding()

    for (const title of ['AI-Powered Design', 'Built-in Compliance', 'Team Collaboration', 'Cloud-Native']) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
    }
    for (const plan of ['Starter', 'Pro', 'Team', 'Enterprise']) {
      expect(screen.getByRole('heading', { name: plan })).toBeInTheDocument()
    }
  })

  it('routes Start Free Trial to the pricing page', async () => {
    renderLanding()
    const user = userEvent.setup()

    await user.click(screen.getAllByRole('button', { name: 'Start Free Trial' })[0])

    expect(screen.getByText('Pricing page stub')).toBeInTheDocument()
  })

  it('opens the Watch Demo placeholder modal', async () => {
    renderLanding()
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: /Watch Demo/ }))

    expect(screen.getByRole('dialog', { name: 'Watch demo' })).toBeInTheDocument()
    expect(screen.getByText(/Placeholder — this flow is pending integration/)).toBeInTheDocument()
  })
})
