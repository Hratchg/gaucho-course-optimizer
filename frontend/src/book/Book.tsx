import { useMemo, useRef, type CSSProperties } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import { easing } from 'maath'
import type { ToggleWeights } from '@/lib/scoring'
import type { GradeQuarter } from '@/types/api'
import PageContent, { PAGE_PX_W, PAGE_PX_H } from './PageContent'
import type { Spread } from './paginate'

export const PAGE_W = 1.28
export const PAGE_H = 1.71
const PAGE_SEGMENTS = 24
const SEG_W = PAGE_W / PAGE_SEGMENTS
const SHEET_GAP = 0.006
const EASING = 0.32
/** drei Html transform mode: world size = css px × distanceFactor / 400. */
const HTML_DISTANCE_FACTOR = (PAGE_W * 400) / PAGE_PX_W

const PARCHMENT = '#f1e8d0'
const PARCHMENT_EDGE = '#e2d5b4'
const LEATHER = '#5a1f2c'

/**
 * Shared skinned-page geometry (Wawa Sensei bone-flip approach): a thin box
 * with width segments, spine edge at x=0, vertices weighted between a chain
 * of bones laid along +x so rotating the chain turns/curls the page.
 */
function createPageGeometry(): THREE.BoxGeometry {
  const geo = new THREE.BoxGeometry(PAGE_W, PAGE_H, 0.003, PAGE_SEGMENTS, 2)
  geo.translate(PAGE_W / 2, 0, 0)

  const position = geo.attributes.position
  const skinIndexes: number[] = []
  const skinWeights: number[] = []
  const vertex = new THREE.Vector3()

  for (let i = 0; i < position.count; i++) {
    vertex.fromBufferAttribute(position, i)
    const x = vertex.x
    const boneIndex = Math.min(Math.max(0, Math.floor(x / SEG_W)), PAGE_SEGMENTS - 1)
    const weight = Math.min(Math.max(x / SEG_W - boneIndex, 0), 1)
    skinIndexes.push(boneIndex, boneIndex + 1, 0, 0)
    skinWeights.push(1 - weight, weight, 0, 0)
  }

  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(skinIndexes, 4))
  geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(skinWeights, 4))
  return geo
}

let pageGeometry: THREE.BoxGeometry | null = null
function getPageGeometry() {
  if (!pageGeometry) pageGeometry = createPageGeometry()
  return pageGeometry
}

function createSheet(materials: THREE.Material[]): { mesh: THREE.SkinnedMesh; bones: THREE.Bone[] } {
  const bones: THREE.Bone[] = []
  for (let i = 0; i <= PAGE_SEGMENTS; i++) {
    const bone = new THREE.Bone()
    bone.position.x = i === 0 ? 0 : SEG_W
    if (i > 0) bones[i - 1].add(bone)
    bones.push(bone)
  }
  const skeleton = new THREE.Skeleton(bones)
  const mesh = new THREE.SkinnedMesh(getPageGeometry(), materials)
  mesh.castShadow = true
  mesh.receiveShadow = true
  mesh.frustumCulled = false
  mesh.add(bones[0])
  mesh.bind(skeleton)
  return { mesh, bones }
}

/** One turnable blank parchment sheet. */
function Sheet({ index, turned, total }: { index: number; turned: boolean; total: number }) {
  const materials = useMemo(() => {
    const edge = new THREE.MeshStandardMaterial({ color: PARCHMENT_EDGE, roughness: 0.95 })
    const face = new THREE.MeshStandardMaterial({ color: PARCHMENT, roughness: 0.9 })
    return [edge, edge, edge, edge, face, face]
  }, [])
  const { mesh, bones } = useMemo(() => createSheet(materials), [materials])
  const group = useRef<THREE.Group>(null)

  useFrame((_, dt) => {
    const delta = Math.min(dt, 0.1)
    const target = turned ? -Math.PI : 0
    easing.dampAngle(bones[0].rotation, 'y', target, EASING, delta)

    // Curl: strongest mid-turn (sin of the root angle), fades when resting.
    const progress = Math.abs(Math.sin(bones[0].rotation.y))
    for (let i = 1; i < bones.length; i++) {
      const falloff = Math.sin((i / bones.length) * Math.PI)
      const curl = (turned ? -1 : -1) * progress * 0.028 * falloff
      easing.dampAngle(bones[i].rotation, 'y', curl, EASING, delta)
    }

    // Stack order: unturned sheets recede on the right, turned sheets pile up
    // on the left with the most recent turn on top.
    if (group.current) {
      const targetZ = turned ? -(total - index) * SHEET_GAP : -(index + 1) * SHEET_GAP
      easing.damp(group.current.position, 'z', targetZ, EASING, delta)
    }
  })

  return (
    <group ref={group}>
      <primitive object={mesh} />
    </group>
  )
}

/** Front cover: pivots at the spine, opens on mount (cover-flip entrance). */
function FrontCover({ total }: { total: number }) {
  const group = useRef<THREE.Group>(null)

  const board = useMemo(() => {
    const geo = new THREE.BoxGeometry(PAGE_W + 0.06, PAGE_H + 0.09, 0.02)
    geo.translate((PAGE_W + 0.06) / 2, 0, 0)
    const leather = new THREE.MeshStandardMaterial({ color: LEATHER, roughness: 0.55, metalness: 0.08 })
    const endpaper = new THREE.MeshStandardMaterial({ color: PARCHMENT, roughness: 0.9 })
    // -z face (5) becomes the visible inside once the cover flips open.
    const mesh = new THREE.Mesh(geo, [leather, leather, leather, leather, leather, endpaper])
    mesh.castShadow = true
    mesh.receiveShadow = true
    return mesh
  }, [])

  useFrame((_, dt) => {
    const delta = Math.min(dt, 0.1)
    if (!group.current) return
    easing.dampAngle(group.current.rotation, 'y', -Math.PI, 0.5, delta)
    easing.damp(group.current.position, 'z', -(total + 1) * SHEET_GAP, 0.5, delta)
  })

  return (
    <group ref={group} position={[0, 0, 0.02]}>
      <primitive object={board} />
    </group>
  )
}

interface BookProps {
  spreads: Spread[]
  spreadIndex: number
  courseId: number
  weights: ToggleWeights
  onWeightsChange: (w: ToggleWeights) => void
  /** True while a page turn (or the entrance) is settling — dims the DOM content. */
  turning: boolean
  topProfGrades?: GradeQuarter[]
}

/**
 * The regal open book: leather covers, gilt-edged parchment sheets flipping
 * on bone chains, and real DOM content (drei Html) resting on the open spread.
 */
export default function Book({ spreads, spreadIndex, courseId, weights, onWeightsChange, turning, topProfGrades }: BookProps) {
  const sheetCount = Math.max(spreads.length - 1, 0)
  const spread = spreads[Math.min(spreadIndex, spreads.length - 1)] ?? null

  const backBoard = useMemo(() => {
    const geo = new THREE.BoxGeometry(PAGE_W + 0.06, PAGE_H + 0.09, 0.02)
    geo.translate((PAGE_W + 0.06) / 2, 0, 0)
    const leather = new THREE.MeshStandardMaterial({ color: LEATHER, roughness: 0.55, metalness: 0.08 })
    const endpaper = new THREE.MeshStandardMaterial({ color: PARCHMENT, roughness: 0.9 })
    // +z face (4) looks up under the right page stack.
    const mesh = new THREE.Mesh(geo, [leather, leather, leather, leather, endpaper, leather])
    mesh.receiveShadow = true
    return mesh
  }, [])

  const contentStyle: CSSProperties = {
    opacity: turning ? 0.25 : 1,
    transition: 'opacity 300ms ease',
    pointerEvents: turning ? 'none' : 'auto',
  }

  return (
    <group rotation={[-0.28, 0, 0]} position={[0, -0.08, 0]}>
      {/* Back cover under the right stack */}
      <primitive object={backBoard} position={[0, 0, -(sheetCount + 2) * SHEET_GAP]} />
      {/* Spine */}
      <mesh position={[0, 0, -(sheetCount + 2) * SHEET_GAP * 0.5]} castShadow>
        <boxGeometry args={[0.05, PAGE_H + 0.09, (sheetCount + 3) * SHEET_GAP + 0.02]} />
        <meshStandardMaterial color={LEATHER} roughness={0.55} metalness={0.08} />
      </mesh>

      <FrontCover total={sheetCount} />

      {Array.from({ length: sheetCount }, (_, i) => (
        <Sheet key={i} index={i} turned={i < spreadIndex} total={sheetCount} />
      ))}

      {/* DOM content lying on the open spread */}
      {spread && (
        <>
          <Html
            transform
            position={[-PAGE_W / 2, 0, 0.03]}
            distanceFactor={HTML_DISTANCE_FACTOR}
            style={contentStyle}
            zIndexRange={[10, 0]}
          >
            <div style={{ width: PAGE_PX_W, height: PAGE_PX_H }}>
              <PageContent
                page={spread.left}
                side="left"
                courseId={courseId}
                weights={weights}
                onWeightsChange={onWeightsChange}
                topProfGrades={topProfGrades}
              />
            </div>
          </Html>
          <Html
            transform
            position={[PAGE_W / 2, 0, 0.03]}
            distanceFactor={HTML_DISTANCE_FACTOR}
            style={contentStyle}
            zIndexRange={[10, 0]}
          >
            <div style={{ width: PAGE_PX_W, height: PAGE_PX_H }}>
              <PageContent
                page={spread.right}
                side="right"
                courseId={courseId}
                weights={weights}
                onWeightsChange={onWeightsChange}
                topProfGrades={topProfGrades}
              />
            </div>
          </Html>
        </>
      )}
    </group>
  )
}
