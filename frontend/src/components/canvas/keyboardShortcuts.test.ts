import { describe, expect, it } from 'vitest'
import { getCanvasShortcut } from './keyboardShortcuts'

function keyEvent(key: string, init: KeyboardEventInit = {}, target?: EventTarget) {
  const event = new KeyboardEvent('keydown', { key, ...init })
  if (target) {
    Object.defineProperty(event, 'target', { value: target })
  }
  return event
}

describe('canvas keyboard shortcuts', () => {
  it('maps copy, paste, undo, redo, duplicate, delete, and escape shortcuts', () => {
    expect(getCanvasShortcut(keyEvent('c', { ctrlKey: true }))).toBe('copy')
    expect(getCanvasShortcut(keyEvent('v', { metaKey: true }))).toBe('paste')
    expect(getCanvasShortcut(keyEvent('z', { metaKey: true }))).toBe('undo')
    expect(getCanvasShortcut(keyEvent('z', { metaKey: true, shiftKey: true }))).toBe('redo')
    expect(getCanvasShortcut(keyEvent('y', { ctrlKey: true }))).toBe('redo')
    expect(getCanvasShortcut(keyEvent('d', { ctrlKey: true }))).toBe('duplicate')
    expect(getCanvasShortcut(keyEvent('Delete'))).toBe('delete')
    expect(getCanvasShortcut(keyEvent('Backspace'))).toBe('delete')
    expect(getCanvasShortcut(keyEvent('Escape'))).toBe('escape')
  })

  it('does not intercept shortcuts while typing in editable controls', () => {
    const input = document.createElement('input')
    const textarea = document.createElement('textarea')
    const select = document.createElement('select')
    const editable = document.createElement('div')
    editable.contentEditable = 'true'

    expect(getCanvasShortcut(keyEvent('c', { ctrlKey: true }, input))).toBeNull()
    expect(getCanvasShortcut(keyEvent('v', { ctrlKey: true }, textarea))).toBeNull()
    expect(getCanvasShortcut(keyEvent('z', { ctrlKey: true }, select))).toBeNull()
    expect(getCanvasShortcut(keyEvent('Backspace', {}, editable))).toBeNull()
  })
})
