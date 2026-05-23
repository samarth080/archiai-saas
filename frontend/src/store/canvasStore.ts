import { create } from 'zustand'

export interface Room {
  id: string
  label: string
  position: { x: number; y: number; z: number }
  size: { w: number; h: number; d: number }
  color: string
}

interface CanvasState {
  rooms: Room[]
  selectedId: string | null
  selectRoom: (id: string) => void
  deselectAll: () => void
  updateRoom: (id: string, patch: Partial<Omit<Room, 'id'>>) => void
  deleteRoom: (id: string) => void
}

export const INITIAL_ROOMS: Room[] = [
  {
    id: 'room-1',
    label: 'Living Room',
    position: { x: 0, y: 1.5, z: 0 },
    size: { w: 6, h: 3, d: 5 },
    color: '#818cf8',
  },
  {
    id: 'room-2',
    label: 'Kitchen',
    position: { x: 7, y: 1.5, z: 0 },
    size: { w: 4, h: 3, d: 4 },
    color: '#34d399',
  },
  {
    id: 'room-3',
    label: 'Master Bedroom',
    position: { x: 0, y: 1.5, z: 6 },
    size: { w: 5, h: 3, d: 5 },
    color: '#fb923c',
  },
  {
    id: 'room-4',
    label: 'Bedroom',
    position: { x: 6, y: 1.5, z: 6 },
    size: { w: 4, h: 3, d: 4 },
    color: '#f472b6',
  },
  {
    id: 'room-5',
    label: 'Bathroom',
    position: { x: 11, y: 1.5, z: 6 },
    size: { w: 3, h: 3, d: 3 },
    color: '#60a5fa',
  },
]

export const useCanvasStore = create<CanvasState>((set) => ({
  rooms: INITIAL_ROOMS,
  selectedId: null,
  selectRoom: (id) => set({ selectedId: id }),
  deselectAll: () => set({ selectedId: null }),
  updateRoom: (id, patch) =>
    set((state) => ({
      rooms: state.rooms.map((r) => (r.id === id ? { ...r, ...patch } : r)),
    })),
  deleteRoom: (id) =>
    set((state) => ({
      rooms: state.rooms.filter((r) => r.id !== id),
    })),
}))
