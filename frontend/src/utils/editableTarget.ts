export function isEditableTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false

  const tagName = target.tagName.toLowerCase()
  if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
    return true
  }

  if (target.isContentEditable) return true

  return Boolean(
    target.closest('[contenteditable="true"], [contenteditable="plaintext-only"], [role="textbox"]'),
  )
}
