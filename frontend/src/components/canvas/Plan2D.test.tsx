import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useCanvasStore, type CanvasLayout, type Room } from '../../store/canvasStore'
import {
  CANVAS_OBJECT_TYPES,
  COMPONENT_REGISTRY,
  type CanvasObjectType,
} from '../../store/componentRegistry'
import { Plan2D } from './Plan2D'
import { EDITOR_PALETTE } from './editorPalette'
import { clientPointToPlan, planViewportMetrics, type PlanBounds } from './plan2dGeometry'

const TEST_ROOM: Room = {
  id: 'room-1',
  label: 'Living Room',
  roomType: 'living_room',
  objectType: 'room',
  floorId: 'floor_0',
  floorLevel: 0,
  position: { x: 4, y: 1.5, z: 4 },
  size: { w: 4, h: 3, d: 4 },
  rotation: { x: 0, y: 0, z: 0 },
  color: '#b3b8e9',
}

function layoutWithRooms(rooms: Room[]): CanvasLayout {
  return {
    version: '1.0',
    building: { floorHeight: 3.2, footprint: { x: 0, z: 0, w: 10, d: 10 } },
    floors: [
      {
        id: 'floor_0',
        name: 'Ground Floor',
        level: 0,
        elevation: 0,
        footprint: { x: 0, z: 0, w: 10, d: 10 },
        rooms,
      },
    ],
    rooms,
  }
}

function cloneTestRoom(overrides: Partial<Room> = {}): Room {
  return {
    ...TEST_ROOM,
    ...overrides,
    position: { ...TEST_ROOM.position, ...overrides.position },
    size: { ...TEST_ROOM.size, ...overrides.size },
    rotation: { ...TEST_ROOM.rotation, ...overrides.rotation },
  }
}

const PLAN_RECT = {
  x: 0,
  y: 0,
  left: 0,
  top: 0,
  right: 600,
  bottom: 600,
  width: 600,
  height: 600,
  toJSON: () => ({}),
} as DOMRect

function planViewBox(svg: Element): PlanBounds {
  const [x, z, w, d] = (svg.getAttribute('viewBox') ?? '').split(' ').map(Number)
  return { x, z, w, d }
}

function pointAt(svg: Element, clientX: number, clientY: number) {
  return clientPointToPlan(clientX, clientY, PLAN_RECT, planViewBox(svg))
}

function mockPlanRect() {
  const svg = screen.getByRole('application', { name: 'Editable floor plan' })
  vi.spyOn(svg, 'getBoundingClientRect').mockReturnValue(PLAN_RECT)
  return svg
}

function hasRenderedPlanText(container: HTMLElement, pattern: RegExp) {
  return [...container.querySelectorAll('svg text')].some((node) =>
    pattern.test(node.textContent ?? ''),
  )
}

beforeEach(() => {
  useCanvasStore.getState().loadLayout(layoutWithRooms([cloneTestRoom()]))
  useCanvasStore.setState({
    selectedId: null,
    selectedFloor: 0,
    viewMode: 'floor_plan',
    snapToGrid: false,
    gridSize: 1,
    showDimensions: false,
    activityLog: [],
    past: [],
    future: [],
    clipboard: null,
    clipboardMessage: null,
    placementMode: null,
    measureMode: false,
    measurePoints: [],
  })
})

describe('Plan2D', () => {
  it('uses a distinct workspace and warm drawing sheet instead of stacked white surfaces', () => {
    render(<Plan2D />)

    expect(screen.getByTestId('plan-workspace-background')).toHaveAttribute(
      'fill',
      expect.stringContaining('plan-workspace-'),
    )
    expect(screen.getByTestId('plan-footprint')).toHaveAttribute(
      'stroke',
      EDITOR_PALETTE.planFrame,
    )
    expect(screen.getByTestId('plan-footprint').getAttribute('fill')).toContain('plan-sheet-')
    expect(Object.values(EDITOR_PALETTE)).not.toContain('#ffffff')
  })

  it('gives spaces a layered surface and reveals dimensions only on selection', () => {
    const { container } = render(<Plan2D />)

    expect(screen.getByTestId('plan-space-surface-room-1')).toBeInTheDocument()
    expect(screen.getByTestId('plan-space-inset-room-1')).toBeInTheDocument()
    expect(hasRenderedPlanText(container, /16\.0 m/)).toBe(false)
    expect(screen.queryByTestId('plan-selection-halo-room-1')).not.toBeInTheDocument()

    act(() => useCanvasStore.getState().selectRoom('room-1'))

    expect(screen.getByTestId('plan-selection-halo-room-1')).toBeInTheDocument()
    expect(hasRenderedPlanText(container, /4\.0 .* 4\.0 m/)).toBe(true)
    expect(screen.getByTestId('plan-footprint-dimensions')).toBeInTheDocument()
    expect(screen.getByTestId('plan-north-compass')).toBeInTheDocument()
  })

  it('renders every registered component type with a safe SVG treatment', () => {
    const rooms = CANVAS_OBJECT_TYPES.map((type, index) => {
      const definition = COMPONENT_REGISTRY[type]
      return cloneTestRoom({
        id: `${type}-${index}`,
        label: definition.label,
        objectType: type,
        roomType: type,
        position: {
          x: 1 + (index % 5) * 1.8,
          y: definition.defaultSize.h / 2,
          z: 1 + Math.floor(index / 5) * 2.5,
        },
        size: definition.defaultSize,
        color: definition.defaultColor,
      })
    })
    useCanvasStore.getState().loadLayout(layoutWithRooms(rooms))

    render(<Plan2D />)

    for (const type of CANVAS_OBJECT_TYPES) {
      expect(document.querySelector(`[data-object-type="${type}"]`)).toBeInTheDocument()
    }
  })

  it('selects on the first left click without moving the object', () => {
    render(<Plan2D />)
    const object = screen.getByTestId('plan-object-room-1')

    expect(object).toHaveStyle({ outline: 'none' })

    fireEvent.pointerDown(object, { button: 0, pointerId: 1, clientX: 300, clientY: 300 })

    const state = useCanvasStore.getState()
    expect(state.selectedId).toBe('room-1')
    expect(state.rooms[0].position).toEqual(TEST_ROOM.position)
    expect(state.activityLog).toHaveLength(0)
  })

  it('moves only after the drag threshold and records one undoable move', () => {
    useCanvasStore.setState({ selectedId: 'room-1' })
    render(<Plan2D />)
    const svg = mockPlanRect()
    const object = screen.getByTestId('plan-object-room-1')

    fireEvent.pointerDown(object, { button: 0, pointerId: 2, clientX: 300, clientY: 300 })
    fireEvent.pointerMove(object, { button: 0, pointerId: 2, clientX: 304, clientY: 300 })
    expect(useCanvasStore.getState().rooms[0].position.x).toBe(4)

    fireEvent.pointerMove(object, { button: 0, pointerId: 2, clientX: 400, clientY: 300 })
    fireEvent.pointerUp(object, { button: 0, pointerId: 2, clientX: 400, clientY: 300 })

    let state = useCanvasStore.getState()
    const scale = planViewportMetrics(PLAN_RECT, planViewBox(svg)).scale
    expect(state.rooms[0].position.x).toBeCloseTo(4 + 100 / scale)
    expect(state.activityLog.filter((entry) => entry.action === 'object.moved')).toHaveLength(1)
    expect(state.past).toHaveLength(1)

    act(() => state.undo())
    state = useCanvasStore.getState()
    expect(state.rooms[0].position.x).toBe(4)
  })

  it('shows eight handles and records one footprint-safe resize', () => {
    useCanvasStore.setState({ selectedId: 'room-1' })
    render(<Plan2D />)
    const svg = mockPlanRect()
    expect(document.querySelectorAll('[data-testid^="plan-resize-room-1-"]')).toHaveLength(8)
    const handle = screen.getByTestId('plan-resize-room-1-se')

    fireEvent.pointerDown(handle, { button: 0, pointerId: 3, clientX: 350, clientY: 350 })
    fireEvent.pointerMove(handle, { button: 0, pointerId: 3, clientX: 400, clientY: 400 })
    fireEvent.pointerUp(handle, { button: 0, pointerId: 3, clientX: 400, clientY: 400 })

    let state = useCanvasStore.getState()
    const pointer = pointAt(svg, 400, 400)
    const expectedW = pointer.x - 2
    const expectedD = pointer.z - 2
    expect(state.rooms[0].size.w).toBeCloseTo(expectedW)
    expect(state.rooms[0].size.d).toBeCloseTo(expectedD)
    expect(state.rooms[0].position.x).toBeCloseTo(2 + expectedW / 2)
    expect(state.activityLog.filter((entry) => entry.action === 'object.resized')).toHaveLength(1)

    act(() => state.undo())
    state = useCanvasStore.getState()
    expect(state.rooms[0].size).toEqual(TEST_ROOM.size)
    expect(state.rooms[0].position).toEqual(TEST_ROOM.position)
  })

  it('renders the selected object last so its handles stay above later objects', () => {
    const wall = cloneTestRoom({
      id: 'wall-late',
      label: 'Wall',
      objectType: 'wall',
      roomType: 'wall',
      size: { w: 6, h: 3, d: 0.15 },
    })
    useCanvasStore.getState().loadLayout(layoutWithRooms([cloneTestRoom(), wall]))
    useCanvasStore.setState({ selectedId: 'room-1' })

    render(<Plan2D />)

    const renderedObjects = document.querySelectorAll('[data-testid^="plan-object-"]')
    expect(renderedObjects[renderedObjects.length - 1]).toHaveAttribute(
      'data-testid',
      'plan-object-room-1',
    )
  })

  it('uses right drag for navigation without moving or deselecting the object', () => {
    useCanvasStore.setState({ selectedId: 'room-1' })
    render(<Plan2D />)
    const svg = mockPlanRect()
    const object = screen.getByTestId('plan-object-room-1')
    const initialViewBox = svg.getAttribute('viewBox')

    fireEvent.pointerDown(object, { button: 2, pointerId: 4, clientX: 300, clientY: 300 })
    fireEvent.pointerMove(svg, { button: 2, pointerId: 4, clientX: 420, clientY: 300 })
    fireEvent.pointerUp(svg, { button: 2, pointerId: 4, clientX: 420, clientY: 300 })

    const state = useCanvasStore.getState()
    expect(state.rooms[0].position).toEqual(TEST_ROOM.position)
    expect(state.selectedId).toBe('room-1')
    expect(state.activityLog).toHaveLength(0)
    expect(svg.getAttribute('viewBox')).not.toBe(initialViewBox)
  })

  it('keeps copy and paste shortcuts available in SVG mode', () => {
    useCanvasStore.setState({ selectedId: 'room-1' })
    render(<Plan2D />)

    fireEvent.keyDown(window, { key: 'c', ctrlKey: true })
    fireEvent.keyDown(window, { key: 'v', ctrlKey: true })

    const state = useCanvasStore.getState()
    expect(state.rooms).toHaveLength(2)
    expect(state.rooms[1].id).not.toBe('room-1')
    expect(state.selectedId).toBe(state.rooms[1].id)
    expect(state.activityLog[0].action).toBe('object.pasted')
  })

  it('places the armed component at the clicked plan coordinate', () => {
    render(<Plan2D />)
    const svg = mockPlanRect()
    act(() => useCanvasStore.getState().setPlacementMode('furniture' as CanvasObjectType))

    fireEvent.pointerDown(svg, { button: 0, pointerId: 5, clientX: 300, clientY: 300 })

    const placed = useCanvasStore.getState().rooms.find((room) => room.objectType === 'furniture')
    const expected = pointAt(svg, 300, 300)
    expect(placed?.position.x).toBeCloseTo(expected.x)
    expect(placed?.position.z).toBeCloseTo(expected.z)
    expect(useCanvasStore.getState().placementMode).toBeNull()
  })
})

describe('Plan2D adaptive room labels', () => {
  it('shows a quiet name by default and dimensions after selection', () => {
    useCanvasStore.getState().loadLayout(layoutWithRooms([cloneTestRoom()]))
    const { container } = render(<Plan2D />)

    expect(screen.getByText('Living Room')).toBeInTheDocument()
    expect(hasRenderedPlanText(container, /4\.0 .* 4\.0 m/)).toBe(false)

    act(() => useCanvasStore.getState().selectRoom('room-1'))

    expect(hasRenderedPlanText(container, /4\.0 .* 4\.0 m/)).toBe(true)
  })

  it('drops the area line first in small rooms, keeping the name', () => {
    useCanvasStore.getState().loadLayout(
      layoutWithRooms([
        cloneTestRoom({ id: 'small', label: 'WC', size: { w: 1.6, h: 3, d: 1.6 } }),
      ]),
    )
    render(<Plan2D />)

    expect(screen.getByText('WC')).toBeInTheDocument()
    expect(screen.queryByText('2.6 m²')).not.toBeInTheDocument()
  })

  it('hides all text in rooms too small for a readable label, leaving the tooltip', () => {
    useCanvasStore.getState().loadLayout(
      layoutWithRooms([
        cloneTestRoom({
          id: 'tiny',
          label: 'Storage Closet',
          size: { w: 0.9, h: 3, d: 0.9 },
        }),
      ]),
    )
    const { container } = render(<Plan2D />)

    expect(screen.queryByText('Storage Closet')).not.toBeInTheDocument()
    const title = container.querySelector('[data-testid="plan-object-tiny"] title')
    expect(title?.textContent).toContain('Storage Closet')
    expect(title?.textContent).toContain('1.0 × 1.0 m')
  })
})
