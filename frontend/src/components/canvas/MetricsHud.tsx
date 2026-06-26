import { useCanvasStore } from '../../store/canvasStore'

export function MetricsHud() {
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)

  const visibleRooms =
    selectedFloor === 'all' ? rooms : rooms.filter((room) => (room.floorLevel ?? 0) === selectedFloor)
  const habitableRooms = visibleRooms.filter((room) => room.objectType === 'room')
  const totalArea = habitableRooms.reduce((sum, room) => sum + room.size.w * room.size.d, 0)

  const visibleFootprintArea =
    selectedFloor === 'all'
      ? floors.reduce((sum, floor) => sum + (floor.footprint ? floor.footprint.w * floor.footprint.d : 0), 0)
      : floors.find((floor) => floor.level === selectedFloor)?.footprint
        ? (() => {
            const footprint = floors.find((floor) => floor.level === selectedFloor)!.footprint!
            return footprint.w * footprint.d
          })()
        : 0

  const efficiency = visibleFootprintArea > 0 ? (totalArea / visibleFootprintArea) * 100 : null

  if (habitableRooms.length === 0) return null

  return (
    <div className="absolute right-4 top-4 z-10 flex flex-col gap-1 rounded border border-gray-200 bg-white/95 px-3 py-2 text-xs text-gray-700 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <span className="text-gray-500">Rooms</span>
        <span className="font-semibold tabular-nums">{habitableRooms.length}</span>
      </div>
      <div className="flex items-center justify-between gap-4">
        <span className="text-gray-500">Total area</span>
        <span className="font-semibold tabular-nums">{totalArea.toFixed(1)} m²</span>
      </div>
      {efficiency !== null && (
        <div className="flex items-center justify-between gap-4">
          <span className="text-gray-500">Footprint use</span>
          <span className="font-semibold tabular-nums">{efficiency.toFixed(0)}%</span>
        </div>
      )}
    </div>
  )
}
