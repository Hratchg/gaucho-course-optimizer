import { useRef, type RefObject } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { FLIGHT_MS, flightPoint, smoothstep } from './flight'

interface PulledBookProps {
  courseCode: string
  courseTitle?: string
  /** Reserved so the landing can still pass a resolved dept. */
  dept?: string
  active: boolean
  exitPoint?: RefObject<THREE.Vector3 | null>
}

/**
 * Closed book that leaves the sphere and travels to the right.
 * The course panel expands after this flight finishes.
 */
export default function PulledBook({ active, exitPoint }: PulledBookProps) {
  const group = useRef<THREE.Group>(null)
  const started = useRef<number | null>(null)

  useFrame((state) => {
    if (!active || !group.current) return
    if (started.current == null) started.current = state.clock.elapsedTime
    const linear = Math.min(1, (state.clock.elapsedTime - started.current) / (FLIGHT_MS / 1000))
    const ease = smoothstep(linear)
    const start: [number, number, number] = exitPoint?.current
      ? [exitPoint.current.x, exitPoint.current.y, exitPoint.current.z]
      : [1.55, 0.12, 0.55]
    const [x, y, z] = flightPoint(ease, start)
    const [nx, , nz] = flightPoint(Math.min(1, ease + 0.04), start)
    group.current.position.set(x, y, z)
    group.current.rotation.set(0.02, Math.atan2(nx - x, nz - z), THREE.MathUtils.lerp(0.22, -0.18, ease))
    group.current.scale.setScalar(THREE.MathUtils.lerp(0.62, 0.95, ease))
  })

  return (
    <group ref={group}>
      <mesh>
        <boxGeometry args={[0.42, 0.58, 0.09]} />
        <meshStandardMaterial color="#8A4630" roughness={0.62} />
      </mesh>
      <mesh position={[-0.2, 0, 0.01]}>
        <boxGeometry args={[0.028, 0.58, 0.096]} />
        <meshStandardMaterial color="#C45C38" roughness={0.5} />
      </mesh>
      <mesh position={[0.04, 0.04, 0.048]}>
        <boxGeometry args={[0.2, 0.09, 0.006]} />
        <meshStandardMaterial color="#F4EFE6" roughness={0.7} />
      </mesh>
    </group>
  )
}
