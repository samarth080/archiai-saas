export function isInternalDataPipelineEnabled() {
  return import.meta.env.VITE_SHOW_DEV_TOOLS === 'true'
}
