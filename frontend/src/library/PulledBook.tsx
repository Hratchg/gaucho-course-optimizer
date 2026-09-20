import { useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import { slotForDept } from './layout'
import { CASE_D } from './Bookcase'

interface PulledBookProps {
  courseCode: string
  courseTitle?: string
  /** Resolved bookcase dept (parent maps course → featured case or GENERAL). */
  dept: string
  /** 0→1 pull-out progress driven by parent state; animated here. */
  active: boolean
}

/**
 * The hero book that slides out of the shelf when a course is chosen.
 * Cover shows the course code; spine is coral. Floats toward the camera.
 */
export default function PulledBook({ courseCode, courseTitle, dept, active }: PulledBookProps) {
  const group = useRef<THREE.Group>(null)
  const progress = useRef(0)
  const slot = slotForDept(dept)

  useFrame((_, dt) => {
    const target = active ? 1 : 0
    progress.current = THREE.MathUtils.damp(progress.current, target, 3.2, dt)
    const p = progress.current
    if (!group.current) return
    // Slide out of the case, drift right of the search card, tilt to camera.
    group.current.position.set(
      slot.position[0] + p * 0.85,
      1.55 + p * 0.3,
      slot.position[2] + CASE_D / 2 + 0.05 + p * 0.8,
    )
    group.current.rotation.set(-0.25 * p, slot.rotationY - p * 0.25, 0)
    group.current.scale.setScalar(1 + p * 0.35)
  })

  return (
    <group ref={group}>
      {/* Book body */}
      <mesh castShadow>
        <boxGeometry args={[0.34, 0.46, 0.07]} />
        <meshStandardMaterial color="#FBF6EC" roughness={0.6} />
      </mesh>
      {/* Cover */}
      <mesh position={[0, 0, 0.037]}>
        <boxGeometry args={[0.34, 0.46, 0.004]} />
        <meshStandardMaterial color="#6C5CE7" roughness={0.5} />
      </mesh>
      {/* Spine */}
      <mesh position={[-0.172, 0, 0]}>
        <boxGeometry args={[0.012, 0.46, 0.074]} />
        <meshStandardMaterial color="#FF5A5F" roughness={0.5} />
      </mesh>
      <Text
        position={[0, 0.06, 0.042]}
        fontSize={0.055}
        color="#FBF6EC"
        anchorX="center"
        maxWidth={0.3}
        textAlign="center"
      >
        {courseCode}
      </Text>
      {courseTitle && (
        <Text
          position={[0, -0.07, 0.042]}
          fontSize={0.026}
          color="#D9D2F5"
          anchorX="center"
          maxWidth={0.28}
          textAlign="center"
        >
          {courseTitle}
        </Text>
      )}
    </group>
  )
}
