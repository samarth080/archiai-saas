import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { DEFAULT_FLOOR, useCanvasStore, type Room } from '../../store/canvasStore'
import { RightPanel } from './RightPanel'

function room(partial: Partial<Room>): Room {
  return {
    id: partial.id ?? 'r1',
    label: partial.label ?? 'Room',
    objectType: 'room',
    roomType: partial.roomType ?? 'living_room',
    floorId: DEFAULT_FLOOR.id,
    floorLevel: 0,
    position: partial.position ?? { x: 2, y: 1.5, z: 2 },
    size: partial.size ?? { w: 4, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#5F6E88',
  } as Room
}

const EAST_ORIENTATION = {
  orientation: {
    facingDirection: 'E',
    roadSide: 'E',
    entrySide: 'E',
    entryWall: 'right',
    daylightRooms: ['living_room'],
  },
  designParams: { plotWidthM: 14, plotDepthM: 18, orientation: 'E' },
  programConstraints: {
    avoidPairs: [['bathroom', 'kitchen']],
    daylightRooms: ['living_room'],
  },
}

beforeEach(() => {
  useCanvasStore.setState({
    rooms: [],
    floors: [{ ...DEFAULT_FLOOR, footprint: { x: 0, z: 0, w: 14, d: 18 } }],
    selectedFloor: 0,
    viewMode: 'floor_plan',
    selectedId: null,
    layoutMetadata: EAST_ORIENTATION,
    activityLog: [],
  })
})

describe('RightPanel site & orientation', () => {
  it('shows facing, entry side, road side, and plot in the no-selection state', () => {
    render(<RightPanel />)

    const site = screen.getByTestId('site-orientation-block')
    expect(site).toHaveTextContent('Facing')
    expect(site).toHaveTextContent('East')
    expect(site).toHaveTextContent('Road side')
    expect(site).toHaveTextContent('14.0 × 18.0 m')
  })

  it('runs daylight and exterior-wall checks for the selected room', () => {
    // Living room touching the west footprint edge — exterior wall satisfied.
    useCanvasStore.setState({
      rooms: [room({ id: 'lr', label: 'Living Room', position: { x: 2, y: 1.5, z: 5 } })],
      selectedId: 'lr',
    })
    render(<RightPanel />)

    const checks = screen.getByTestId('room-checks')
    expect(checks).toHaveTextContent('Exterior wall')
    expect(checks).toHaveTextContent('Daylight priority')
    expect(checks.textContent?.match(/Satisfied/g)?.length).toBeGreaterThanOrEqual(2)
  })

  it('flags an interior daylight-priority room with a warning', () => {
    useCanvasStore.setState({
      rooms: [room({ id: 'lr', label: 'Living Room', position: { x: 7, y: 1.5, z: 9 } })],
      selectedId: 'lr',
    })
    render(<RightPanel />)

    expect(screen.getByTestId('room-checks')).toHaveTextContent('Warning')
  })

  it('reports avoid-adjacency status for a kitchen next to a bathroom', () => {
    useCanvasStore.setState({
      rooms: [
        room({ id: 'k', label: 'Kitchen', roomType: 'kitchen', position: { x: 2, y: 1.5, z: 2 } }),
        room({ id: 'b', label: 'Bathroom', roomType: 'bathroom', position: { x: 6, y: 1.5, z: 2 } }),
      ],
      selectedId: 'k',
    })
    render(<RightPanel />)

    const checks = screen.getByTestId('room-checks')
    expect(checks).toHaveTextContent('Kept apart from bathroom')
    expect(checks).toHaveTextContent('Warning')
  })
})
