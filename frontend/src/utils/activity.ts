const ACTION_LABELS: Record<string, string> = {
  'project.created': 'Created project',
  'project.updated': 'Updated project',
  'project.deleted': 'Deleted project',
  'project.duplicated': 'Duplicated project',
  'project.exported': 'Exported project',
  'project.shared': 'Created read-only share link',
  'project.share_revoked': 'Revoked share link',
  'design.generated': 'Generated layout',
  'design.refined': 'Refined layout',
  'design.draft_saved': 'Auto-saved draft',
  'layout.saved': 'Saved layout',
  'workspace.created': 'Created workspace',
  'workspace.updated': 'Updated workspace',
  'workspace.deleted': 'Deleted workspace',
  'workspace.member_added': 'Added workspace member',
  'workspace.member_role_changed': 'Changed workspace member role',
  'workspace.member_removed': 'Removed workspace member',
}

export function activityLabel(action: string): string {
  return ACTION_LABELS[action] ?? action
}

