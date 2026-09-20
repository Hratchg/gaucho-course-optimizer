import { useLayoutEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { useGLTF, useTexture } from '@react-three/drei'
import type { BookcaseSlot } from './layout'
import { CASE_H, DeptPlaque } from './Bookcase'

interface GeneratedBookcaseProps {
  url: string
  slot: BookcaseSlot
}

/**
 * Drop-in replacement for the procedural Bookcase: a Tripo/Meshy GLB
 * normalized to CASE_H, oak PBR applied to untextured drafts, brass plaque on top.
 */
export default function GeneratedBookcase({ url, slot }: GeneratedBookcaseProps) {
  const gltf = useGLTF(url)
  const root = useRef<THREE.Group>(null)
  const [woodMap, woodRough] = useTexture(['/3d/wood-diff.jpg', '/3d/wood-rough.jpg'])

  const source = useMemo(() => gltf.scene.clone(true), [gltf.scene])

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
      if (obj instanceof THREE.Mesh) {
        obj.material = wood
        obj.castShadow = true
        obj.receiveShadow = true
      }
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
      {/* Tripo drafts face +X; rotate so empty shelves look down the aisle. */}
      <group ref={root} rotation-y={-Math.PI / 2} />
      <DeptPlaque label={slot.dept} />
    </group>
  )
}
