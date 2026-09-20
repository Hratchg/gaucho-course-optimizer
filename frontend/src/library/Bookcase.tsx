import { useMemo } from 'react'
import * as THREE from 'three'
import { useTexture, Text } from '@react-three/drei'
import type { BookcaseSlot } from './layout'

/** Deterministic PRNG so book colors/sizes are stable per bookcase. */
function mulberry32(seed: number) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const BOOK_PALETTE = [
  '#B8433F', '#89547C', '#3E5F8A', '#437A6B', '#B08D3E',
  '#6C5CE7', '#20BFA9', '#C96A4A', '#54577C', '#7E5B3A',
]

export const CASE_W = 2.4
export const CASE_H = 3.1
export const CASE_D = 0.45
const SHELF_COUNT = 5
const SHELF_T = 0.045

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

  const books = useMemo(() => {
    const rand = mulberry32(seed)
    const rows: { pos: [number, number, number]; scale: [number, number, number]; color: string }[] = []
    const innerW = CASE_W - 0.2
    for (let s = 0; s < SHELF_COUNT; s++) {
      const shelfY = 0.28 + s * ((CASE_H - 0.5) / SHELF_COUNT)
      let x = -innerW / 2 + 0.06
      while (x < innerW / 2 - 0.1) {
        const w = 0.045 + rand() * 0.05
        const h = 0.32 + rand() * 0.14
        const d = CASE_D - 0.14 - rand() * 0.06
        if (rand() > 0.08) {
          rows.push({
            pos: [x + w / 2, shelfY + h / 2 + SHELF_T / 2, -0.02],
            scale: [w, h, d],
            color: BOOK_PALETTE[Math.floor(rand() * BOOK_PALETTE.length)],
          })
        }
        x += w + 0.006 + (rand() < 0.06 ? 0.09 : 0)
      }
    }
    return rows
  }, [seed])

  const bookGeo = useMemo(() => new THREE.BoxGeometry(1, 1, 1), [])
  const bookMat = useMemo(
    () => new THREE.MeshStandardMaterial({ roughness: 0.75, metalness: 0.02 }),
    [],
  )

  const setInstances = (mesh: THREE.InstancedMesh | null) => {
    if (!mesh) return
    const m = new THREE.Matrix4()
    const q = new THREE.Quaternion()
    const v = new THREE.Vector3()
    const sc = new THREE.Vector3()
    books.forEach((b, i) => {
      v.set(...b.pos)
      sc.set(...b.scale)
      m.compose(v, q, sc)
      mesh.setMatrixAt(i, m)
      mesh.setColorAt(i, new THREE.Color(b.color))
    })
    mesh.instanceMatrix.needsUpdate = true
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
  }

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

      {/* Shelves */}
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

      {/* Books */}
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
