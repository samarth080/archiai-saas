import { useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { Scene } from './Scene'
import { RoomMesh } from './RoomMesh'
import { useCanvasStore } from '../../store/canvasStore'

interface Canvas3DProps {
  className?: string
}

export function Canvas3D({ className }: Canvas3DProps) {
  const orbitRef = useRef<{ enabled: boolean }>(null)
  const rooms = useCanvasStore((s) => s.rooms)
  const deselectAll = useCanvasStore((s) => s.deselectAll)

  return (
    <div className={className} style={{ background: '#f1f5f9' }}>
      <Canvas
        camera={{ position: [10, 12, 10] as [number, number, number], fov: 50 }}
        onClick={deselectAll}
      >
        <Scene orbitRef={orbitRef} />
        {rooms.map((r) => (
          <RoomMesh key={r.id} room={r} orbitRef={orbitRef} />
        ))}
      </Canvas>
    </div>
  )
}
