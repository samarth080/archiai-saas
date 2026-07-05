import { isEditableTarget } from '../../utils/editableTarget'

export type CanvasShortcut =
  | 'copy'
  | 'paste'
  | 'undo'
  | 'redo'
  | 'duplicate'
  | 'delete'
  | 'escape'

export function getCanvasShortcut(event: KeyboardEvent): CanvasShortcut | null {
  if (isEditableTarget(event.target)) return null

  const key = event.key.toLowerCase()
  const command = event.ctrlKey || event.metaKey

  if (command && key === 'c') return 'copy'
  if (command && key === 'v') return 'paste'
  if (command && key === 'z' && event.shiftKey) return 'redo'
  if (command && key === 'z') return 'undo'
  if (event.ctrlKey && key === 'y') return 'redo'
  if (command && key === 'd') return 'duplicate'
  if (event.key === 'Delete' || event.key === 'Backspace') return 'delete'
  if (event.key === 'Escape') return 'escape'

  return null
}
