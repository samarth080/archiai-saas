import type {
  AssignableWorkspaceRole,
  TeamMember,
} from '../../services/workspace.service'
import { Button } from '../ui/Button'

interface MemberListProps {
  members: TeamMember[]
  canManage: boolean
  onRoleChange: (member: TeamMember, role: AssignableWorkspaceRole) => void
  onRemove: (member: TeamMember) => void
}

export function MemberList({ members, canManage, onRoleChange, onRemove }: MemberListProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-ink/10 bg-graphite-800">
      {members.map((member) => (
        <div
          key={member.id}
          className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/10 px-4 py-3 last:border-b-0"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-ink">{member.name}</p>
            <p className="truncate text-xs text-muted-light">{member.email}</p>
          </div>
          {canManage && member.role !== 'owner' ? (
            <div className="flex items-center gap-2">
              <label className="sr-only" htmlFor={`role-${member.id}`}>
                Role for {member.name}
              </label>
              <select
                id={`role-${member.id}`}
                value={member.role}
                onChange={(event) =>
                  onRoleChange(member, event.target.value as AssignableWorkspaceRole)
                }
                className="rounded border border-ink/15 bg-graphite-700 px-2 py-1.5 text-sm capitalize focus:border-transparent focus:outline-none focus:ring-2 focus:ring-ink/30"
              >
                <option value="admin">Admin</option>
                <option value="editor">Editor</option>
                <option value="viewer">Viewer</option>
              </select>
              <Button type="button" variant="secondary" onClick={() => onRemove(member)}>
                Remove
              </Button>
            </div>
          ) : (
            <span className="text-sm capitalize text-muted-light">{member.role}</span>
          )}
        </div>
      ))}
    </div>
  )
}
