import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { TeamMember } from '../../services/workspace.service'
import { MemberList } from './MemberList'

const members: TeamMember[] = [
  {
    id: 'owner-member',
    workspace_id: 'workspace-1',
    user_id: 'user-1',
    email: 'owner@example.com',
    name: 'Owner',
    role: 'owner',
    created_at: '2026-05-31T00:00:00Z',
  },
  {
    id: 'editor-member',
    workspace_id: 'workspace-1',
    user_id: 'user-2',
    email: 'editor@example.com',
    name: 'Editor',
    role: 'editor',
    created_at: '2026-05-31T00:00:00Z',
  },
]

describe('MemberList', () => {
  it('lets managers change and remove non-owner members', async () => {
    const onRoleChange = vi.fn()
    const onRemove = vi.fn()
    const user = userEvent.setup()
    render(
      <MemberList
        members={members}
        canManage
        onRoleChange={onRoleChange}
        onRemove={onRemove}
      />,
    )

    await user.selectOptions(screen.getByLabelText('Role for Editor'), 'viewer')
    await user.click(screen.getByRole('button', { name: 'Remove' }))

    expect(onRoleChange).toHaveBeenCalledWith(members[1], 'viewer')
    expect(onRemove).toHaveBeenCalledWith(members[1])
    expect(screen.getByText('owner')).toBeInTheDocument()
  })

  it('shows read-only roles to members without management permission', () => {
    render(
      <MemberList
        members={members}
        canManage={false}
        onRoleChange={vi.fn()}
        onRemove={vi.fn()}
      />,
    )

    expect(screen.queryByRole('button', { name: 'Remove' })).not.toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})
