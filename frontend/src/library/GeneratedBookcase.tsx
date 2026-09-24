import { useLayoutEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { useGLTF, useTexture } from '@react-three/drei'
import type { BookcaseSlot } from './layout'
import { CASE_H } from './Bookcase'
import BookInstances from './BookInstances'
import { generatedShelfLayout, materialHasColorMap, packShelfBooks } from './books'

interface GeneratedBookcaseProps {
  url: string
  slot: BookcaseSlot
  seed: number
}

/**
 * Drop-in replacement for the procedural Bookcase: a Tripo/Meshy GLB
 * normalized to CASE_H, oak PBR applied to untextured drafts, brass plaque
 * on top, and the same instanced books packed onto measured shelf tops.
 */
export default function GeneratedBookcase({ url, slot, seed }: GeneratedBookcaseProps) {
  const gltf = useGLTF(url)
  const root = useRef<THREE.Group>(null)
  const [woodMap, woodRough] = useTexture(['/3d/wood-diff.jpg', '/3d/wood-rough.jpg'])

  const source = useMemo(() => gltf.scene.clone(true), [gltf.scene])

  const books = useMemo(() => {
    const layout = generatedShelfLayout(CASE_H)
    return packShelfBooks({
      seed,
      shelfYs: layout.shelfYs,
      innerW: layout.innerW,
      caseD: layout.caseD,
      maxHeights: layout.maxHeights,
    })
  }, [seed])

  useLayoutEffect(() => {
    const map = woodMap.clone()
    const rough = woodRough.clone()
    map.wrapS = map.wrapT = THREE.RepeatWrapping
    rough.wrapS = rough.wrapT = THREE.RepeatWrapping
    map.repeat.set(2, 3)
    rough.repeat.set(2, 3)
    map.colorSpace = THREE.SRGBColorSpace

    const wood = new THREE.MeshStandardMaterial({
      map,
      roughnessMap: rough,
      roughness: 0.85,
      color: '#9a7b57',
    })

    source.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return
      obj.castShadow = true
      obj.receiveShadow = true
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material]
      const textured = materialHasColorMap(mats)
      // Keep Tripo/Meshy PBR when the web-app export already has maps.
      if (!textured) obj.material = wood
    })

    const box = new THREE.Box3().setFromObject(source)
    const size = box.getSize(new THREE.Vector3())
    const center = box.getCenter(new THREE.Vector3())
    const s = CASE_H / Math.max(size.y, 0.001)
    source.scale.setScalar(s)
    source.position.set(-center.x * s, -box.min.y * s, -center.z * s)

    if (!root.current) return
    root.current.clear()
    root.current.add(source)
  }, [source, woodMap, woodRough])

  return (
    <group position={slot.position} rotation-y={slot.rotationY}>
      {/* Studio export is already aisle-facing; untextured API drafts needed -PI/2. */}
      <group ref={root} />
      <BookInstances books={books} />
    </group>
  )
}
