/**
 * Hand-written TypeScript mirror of the backend MVP contracts (workflow Step 0.3):
 * backend/app/schemas/{requirements,layout_plan,quality_report}.py
 *
 * COORDINATE CONVENTION (same statement as layout_plan.py, never restated
 * differently): units are METERS, origin at the plot's NW corner, +x EAST,
 * +y SOUTH, north-up. Rotation is limited to 0 | 90 | 180 | 270.
 *
 * Keep field names snake_case to match the wire format exactly.
 */

export type BuildingType =
  | 'house' | 'apartment' | 'villa' | 'duplex' | 'clinic' | 'office' | 'other'

export type RoomType =
  | 'bedroom' | 'master_bedroom' | 'bathroom' | 'kitchen' | 'living_room'
  | 'dining' | 'balcony' | 'entry' | 'pooja_room' | 'study' | 'utility' | 'parking'

export type Facing = 'north' | 'south' | 'east' | 'west'

export interface RoomRequest { type: RoomType; count: number }
export interface AdjacencyPref { room_a: RoomType; room_b: RoomType; strength: 'must' | 'should' }
export interface AvoidPair { room_a: RoomType; room_b: RoomType }
export interface PlotSpec { width_m: number | null; depth_m: number | null }

export interface RequirementsSpec {
  building_type: BuildingType
  floors: number
  rooms: RoomRequest[]
  adjacency: AdjacencyPref[]
  avoid_adjacency: AvoidPair[]
  plot: PlotSpec
  facing: Facing | null
  missing_info: string[]
}

export type Rotation = 0 | 90 | 180 | 270

export interface PlanPlot { width_m: number; depth_m: number; facing: Facing }

export interface PlanRoom {
  id: string
  type: RoomType
  label: string
  x: number
  y: number
  w: number
  h: number
  rotation: Rotation
}

export interface Wall { id: string; x1: number; y1: number; x2: number; y2: number; thickness: number }
export interface Door { id: string; wall_ref: string; offset: number; width: number }

export interface LayoutPlan {
  plot: PlanPlot
  rooms: PlanRoom[]
  walls: Wall[]
  doors: Door[]
}

export interface Violation { code: string; room_ids: string[]; message: string }
export interface QualityWarning {
  code: string
  message: string
  severity: 'info' | 'warn'
  rule: 'generic' | 'vastu'
}
export interface QualityReport {
  score: number
  hard_violations: Violation[]
  warnings: QualityWarning[]
}

export type ClarificationRoute = 'vague' | 'generate' | 'conflict'

export interface ExtractResponse {
  requirements: RequirementsSpec
  route: ClarificationRoute
  questions: string[]
  optional_missing: string[]
  understood_summary: string[]
}

export interface HardQualitySnapshot {
  valid: boolean
  hard_violations: Violation[]
}

export interface GenerateMvpResponse {
  requirements: RequirementsSpec
  layout: LayoutPlan
  quality: HardQualitySnapshot
  defaults_applied: string[]
  designId: string | null
  designVersionId: string | null
}

export interface MvpVersionResponse {
  id: string
  designId: string
  projectId: string
  versionNumber: number
  prompt: string | null
  requirements: RequirementsSpec
  layout: LayoutPlan
  quality: HardQualitySnapshot
  createdAt: string
}

/** Editor-side clamp minima - subset of backend ROOM_SIZING (keep in sync). */
export const ROOM_MIN_SIZE: Record<RoomType, { minW: number; minD: number }> = {
  bedroom: { minW: 3.0, minD: 3.0 },
  master_bedroom: { minW: 3.3, minD: 3.3 },
  bathroom: { minW: 1.5, minD: 2.1 },
  kitchen: { minW: 2.4, minD: 3.0 },
  living_room: { minW: 3.3, minD: 3.6 },
  dining: { minW: 2.7, minD: 3.0 },
  balcony: { minW: 1.2, minD: 2.4 },
  entry: { minW: 1.2, minD: 1.5 },
  pooja_room: { minW: 1.2, minD: 1.5 },
  study: { minW: 2.4, minD: 2.7 },
  utility: { minW: 1.5, minD: 1.8 },
  parking: { minW: 2.7, minD: 5.0 },
}
