import { useMemo } from 'react'
import * as THREE from 'three'
import { useTexture, Text } from '@react-three/drei'
import type { BookcaseSlot } from './layout'
import {
  CASE_D,
  CASE_H,
  CASE_W,
  SHELF_COUNT,
  SHELF_T,
  packShelfBooks,
  proceduralShelfYs,
  useBookInstances,
} from './books'

export { CASE_D, CASE_H, CASE_W } from './books'

interface BookcaseProps {
  slot: BookcaseSlot
  seed: number
}

/**
 * Procedural bookcase: oak PBR carcass, five shelves, rows of instanced
 * books with per-case deterministic variation, and a brass dept plaque.
 */
export default function Bookcase({ slot, seed }: BookcaseProps) {
  const [woodMap, woodRough] = useTexture(['/3d/wood-diff.jpg', '/3d/wood-rough.jpg'])
  woodMap.wrapS = woodMap.wrapT = THREE.RepeatWrapping
  woodRough.wrapS = woodRough.wrapT = THREE.RepeatWrapping
  woodMap.colorSpace = THREE.SRGBColorSpace

  const woodMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: woodMap,
        roughnessMap: woodRough,
        roughness: 0.85,
        metalness: 0.0,
      }),
    [woodMap, woodRough],
  )

  const books = useMemo(
    () =>
      packShelfBooks({
        seed,
        shelfYs: proceduralShelfYs(),
        innerW: CASE_W - 0.2,
        caseD: CASE_D,
      }),
    [seed],
  )
  const { bookGeo, bookMat, setInstances } = useBookInstances(books)

  return (
    <group position={slot.position} rotation-y={slot.rotationY}>
      {/* Carcass: two sides, top, bottom, back */}
      <mesh material={woodMat} position={[-CASE_W / 2 + 0.05, CASE_H / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.1, CASE_H, CASE_D]} />
      </mesh>
      <mesh material={woodMat} position={[CASE_W / 2 - 0.05, CASE_H / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.1, CASE_H, CASE_D]} />
      </mesh>
      <mesh material={woodMat} position={[0, CASE_H - 0.05, 0]} castShadow receiveShadow>
        <boxGeometry args={[CASE_W, 0.1, CASE_D]} />
      </mesh>
      <mesh material={woodMat} position={[0, 0.09, 0]} castShadow receiveShadow>
        <boxGeometry args={[CASE_W, 0.18, CASE_D]} />
      </mesh>
      <mesh material={woodMat} position={[0, CASE_H / 2, -CASE_D / 2 + 0.02]} receiveShadow>
        <boxGeometry args={[CASE_W, CASE_H, 0.04]} />
      </mesh>

      {Array.from({ length: SHELF_COUNT }, (_, s) => (
        <mesh
          key={s}
          material={woodMat}
          position={[0, 0.28 + s * ((CASE_H - 0.5) / SHELF_COUNT), 0]}
          castShadow
          receiveShadow
        >
          <boxGeometry args={[CASE_W - 0.16, SHELF_T, CASE_D - 0.08]} />
        </mesh>
      ))}

      <instancedMesh ref={setInstances} args={[bookGeo, bookMat, books.length]} castShadow />

      <DeptPlaque label={slot.dept} />
    </group>
  )
}

/** Shared brass plaque so generated GLB cases keep the same department label. */
export function DeptPlaque({ label }: { label: string }) {
  return (
    <>
      <mesh position={[0, CASE_H + 0.02, CASE_D / 2 - 0.1]} castShadow>
        <boxGeometry args={[1.02, 0.24, 0.03]} />
        <meshStandardMaterial
          color="#c4a35a"
          metalness={0.55}
          roughness={0.4}
          emissive="#8a6a28"
          emissiveIntensity={0.55}
        />
      </mesh>
      <Text
        position={[0, CASE_H + 0.02, CASE_D / 2 - 0.078]}
        fontSize={0.125}
        color="#f6ecd0"
        outlineWidth={0.016}
        outlineColor="#1c1408"
        anchorX="center"
        anchorY="middle"
        letterSpacing={0.08}
      >
        {label}
      </Text>
    </>
  )
}
