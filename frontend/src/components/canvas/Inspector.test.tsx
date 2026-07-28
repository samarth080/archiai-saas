import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useCanvasStore, type Room } from '../../store/canvasStore'
import { InspectorProperties } from './Inspector'

const ROOM: Room = {
  id: 'room-1',
  label: 'Living Room',
  roomType: 'living_room',
  objectType: 'room',
  floorId: 'floor_0',
  floorLevel: 0,
  position: { x: 4, y: 1.5, z: 4 },
  size: { w: 4, h: 3, d: 5 },
  rotation: { x: 12, y: 0, z: 8 },
  color: '#5F6E88',
}

function InspectorHarness() {
  const room = useCanvasStore((state) => state.rooms[0])
  return room ? <InspectorProperties room={room} /> : null
}

beforeEach(() => {
  useCanvasStore.setState({
    rooms: [{ ...ROOM, position: { ...ROOM.position }, size: { ...ROOM.size }, rotation: { ...ROOM.rotation } }],
    floors: [{
      id: 'floor_0',
      name: 'Ground Floor',
      level: 0,
      elevation: 0,
      footprint: { x: 0, z: 0, w: 10, d: 10 },
      rooms: [],
    }],
    activityLog: [],
    past: [],
    future: [],
  })
})

describe('Inspector room rotation', () => {
  it('locks canonical rooms to Y-axis quarter turns', () => {
    render(<InspectorHarness />)

    const xRotation = screen.getByRole('spinbutton', { name: 'Rotation X' })
    const yRotation = screen.getByRole('spinbutton', { name: 'Rotation Y' })
    const zRotation = screen.getByRole('spinbutton', { name: 'Rotation Z' })

    expect(xRotation).toBeDisabled()
    expect(zRotation).toBeDisabled()
    expect(yRotation).toHaveAttribute('step', '90')
    expect(screen.queryByRole('button', { name: '+15 deg' })).not.toBeInTheDocument()

    fireEvent.change(yRotation, { target: { value: '46' } })

    expect(useCanvasStore.getState().rooms[0].rotation).toEqual({ x: 0, y: 90, z: 0 })
    expect(screen.getByText('Rooms stay axis-aligned and rotate in 90-degree steps.')).toBeInTheDocument()
  })
})
