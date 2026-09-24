import { useRef, type RefObject } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { FLIGHT_MS, RETURN_MS, flightPoint, smoothstep } from './flight'
import { getSpineMaterials, useBookGeometry } from './books'

export interface BorrowedBook {
  claimKey: number
  index: number
  variant: number
  color: string
  /** World-space size, already multiplied by the sphere's current scale. */
  scale: [number, number, number]
  position: [number, number, number]
  quaternion: [number, number, number, number]
}

interface PulledBookProps {
  direction: 'out' | 'back'
  claimKey: number
  look: BorrowedBook
  /** Live world position of the empty slot, so a return can meet the sphere. */
  slot: RefObject<THREE.Vector3 | null>
}

const FACE = new THREE.Quaternion()

/**
 * One sphere book, lifted out with the same spine, pages, and proportions.
 * `out` carries it to the course panel. `back` flies that same book home.
 */
export default function PulledBook({ direction, claimKey, look, slot }: PulledBookProps) {
  const group = useRef<THREE.Group>(null)
  const started = useRef<number | null>(null)
  const materials = useRef<THREE.Material[] | null>(null)
  const built = useRef<string>('')

  const geo = useBookGeometry()

  useFrame((state) => {
    if (!group.current) return
    const id = `${look.claimKey}:${look.index}`
    if (built.current !== id) {
      built.current = id
      started.current = null
      materials.current?.forEach((material) => material.dispose())
      const tint = new THREE.Color(look.color)
      materials.current = getSpineMaterials()[look.variant].map((material) => {
        const next = material.clone()
        if (next instanceof THREE.MeshStandardMaterial) next.color.multiply(tint)
        return next
      })
      const mesh = group.current.children[0] as THREE.Mesh
      mesh.material = materials.current
      mesh.scale.set(look.scale[0], look.scale[1], look.scale[2])
    }

    if (direction === 'out' && look.claimKey !== claimKey) return
    if (started.current == null) started.current = state.clock.elapsedTime
    const duration = (direction === 'back' ? RETURN_MS : FLIGHT_MS) / 1000
    const linear = Math.min(1, (state.clock.elapsedTime - started.current) / duration)
    const ease = smoothstep(linear)
    const travel = direction === 'back' ? 1 - ease : ease

    const home: [number, number, number] = direction === 'back' && slot.current
      ? [slot.current.x, slot.current.y, slot.current.z]
      : look.position
    const [x, y, z] = flightPoint(travel, home)
    group.current.position.set(x, y, z)

    const from = new THREE.Quaternion(...look.quaternion)
    const orient = from.clone().slerp(FACE, travel)
    group.current.quaternion.copy(orient)

    const grow = THREE.MathUtils.lerp(1, 2.6, travel)
    group.current.scale.setScalar(grow)
  })

  return (
    <group ref={group}>
      <mesh geometry={geo} />
    </group>
  )
}
