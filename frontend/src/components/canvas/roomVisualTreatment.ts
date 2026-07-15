import type {
  CanvasObjectType,
  ComponentDefinition,
} from '../../store/componentRegistry'

export interface RoomVisualTreatment {
  opacity: number
  depthWrite: boolean
  roughness: number
  metalness: number
  emissive: string
  emissiveIntensity: number
  edgeColor: string
}

export function roomVisualTreatment(
  definition: ComponentDefinition,
  objectType: CanvasObjectType,
  selected: boolean,
  planView: boolean,
): RoomVisualTreatment {
  const opacity =
    objectType === 'window'
      ? 0.48
      : objectType === 'door'
        ? 0.74
        : definition.renderingTreatment === 'thin'
          ? 0.7
          : definition.renderingTreatment === 'slab'
            ? 0.58
            : selected
              ? 0.96
              : planView && definition.category === 'space'
                ? 0.68
                : definition.category === 'space'
                  ? 0.84
                  : 0.78

  return {
    opacity,
    depthWrite: opacity > 0.75,
    roughness: definition.category === 'opening' ? 0.48 : 0.72,
    metalness: definition.category === 'structure' ? 0.07 : 0.02,
    emissive: selected ? '#6354b8' : '#000000',
    emissiveIntensity: selected ? 0.24 : 0,
    edgeColor: selected ? '#6354b8' : '#3f4b5f',
  }
}
