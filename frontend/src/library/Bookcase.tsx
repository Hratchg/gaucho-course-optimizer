import { useMemo } from 'react'
import * as THREE from 'three'
import { useTexture } from '@react-three/drei'
import type { BookcaseSlot } from './layout'
import BookInstances from './BookInstances'
import {
  CASE_D,
  CASE_H,
  CASE_W,
  SHELF_COUNT,
  SHELF_T,
  packShelfBooks,
  proceduralShelfYs,
} from './books'

export { CASE_D, CASE_H, CASE_W } from './books'

interface BookcaseProps {
  slot: BookcaseSlot
  seed: number
  width?: number
  height?: number
  depth?: number
  shelves?: number
}

/**
 * Procedural bookcase: oak PBR carcass, shelves, and instanced books.
 * Size defaults to the original aisle case; the landing passes hero dimensions.
 */
export default function Bookcase({
  slot,
  seed,
  width = CASE_W,
  height = CASE_H,
  depth = CASE_D,
  shelves = SHELF_COUNT,
}: BookcaseProps) {
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

  const shelfYs = useMemo(() => proceduralShelfYs(height, shelves), [height, shelves])
  const books = useMemo(
    () =>
      packShelfBooks({
        seed,
        shelfYs,
        innerW: width - 0.2,
        caseD: depth,
        maxHeights: shelfYs.map((y, i) => {
          const next = shelfYs[i + 1] ?? height - 0.08
          return Math.max(0.18, next - y - 0.04)
        }),
      }),
    [seed, shelfYs, width, depth, height],
  )

  return (
    <group position={slot.position} rotation-y={slot.rotationY}>
      <mesh material={woodMat} position={[-width / 2 + 0.05, height / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.1, height, depth]} />
      </mesh>
      <mesh material={woodMat} position={[width / 2 - 0.05, height / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.1, height, depth]} />
      </mesh>
      <mesh material={woodMat} position={[0, height - 0.05, 0]} castShadow receiveShadow>
        <boxGeometry args={[width, 0.1, depth]} />
      </mesh>
      <mesh material={woodMat} position={[0, 0.09, 0]} castShadow receiveShadow>
        <boxGeometry args={[width, 0.18, depth]} />
      </mesh>
      <mesh material={woodMat} position={[0, height / 2, -depth / 2 + 0.02]} receiveShadow>
        <boxGeometry args={[width, height, 0.04]} />
      </mesh>

      {shelfYs.map((y) => (
        <mesh key={y} material={woodMat} position={[0, y, 0]} castShadow receiveShadow>
          <boxGeometry args={[width - 0.16, SHELF_T, depth - 0.08]} />
        </mesh>
      ))}

      <BookInstances books={books} />
    </group>
  )
}
