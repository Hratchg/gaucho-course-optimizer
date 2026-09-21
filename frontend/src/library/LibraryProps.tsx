import { useLayoutEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { useGLTF } from '@react-three/drei'
import { materialHasColorMap } from './books'
import { PROP_URLS } from './generatedAssets'

const BRASS = new THREE.MeshStandardMaterial({
  color: '#b98a2e',
  metalness: 0.85,
  roughness: 0.35,
  emissive: '#3a2a08',
  emissiveIntensity: 0.35,
})

const OAK = new THREE.MeshStandardMaterial({ color: '#8a6a42', roughness: 0.8, metalness: 0.02 })

/**
 * Normalizes an untextured Meshy preview: applies the override material,
 * scales to targetH, and re-anchors (bottom at y=0 when grounded, else center).
 */
function useProp(url: string, targetH: number, override: THREE.Material, grounded: boolean) {
  const gltf = useGLTF(url)
  const root = useRef<THREE.Group>(null)
  const source = useMemo(() => gltf.scene.clone(true), [gltf.scene])

  useLayoutEffect(() => {
    source.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return
      obj.castShadow = true
      obj.receiveShadow = true
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material]
      if (!materialHasColorMap(mats)) obj.material = override
    })
    const box = new THREE.Box3().setFromObject(source)
    const size = box.getSize(new THREE.Vector3())
    const center = box.getCenter(new THREE.Vector3())
    const s = targetH / Math.max(size.y, 0.001)
    source.scale.setScalar(s)
    source.position.set(
      -center.x * s,
      grounded ? -box.min.y * s : -center.y * s,
      -center.z * s,
    )
    if (!root.current) return
    root.current.clear()
    root.current.add(source)
  }, [source, targetH, override, grounded])

  return root
}

function Chandelier({ position }: { position: [number, number, number] }) {
  const root = useProp(PROP_URLS.chandelier, 1.5, BRASS, false)
  return (
    <group position={position}>
      {/* Hanging rod up to the (implied) ceiling */}
      <mesh position={[0, 1.6, 0]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, 2.4, 8]} />
        <meshStandardMaterial color="#6e5518" metalness={0.8} roughness={0.4} />
      </mesh>
      <group ref={root} />
      <pointLight position={[0, -0.1, 0]} intensity={2.6} distance={7} color="#ffc93c" />
    </group>
  )
}

function LibraryLadder({ position, rotationY }: { position: [number, number, number]; rotationY: number }) {
  const root = useProp(PROP_URLS.ladder, 2.9, OAK, true)
  return (
    <group position={position} rotation-y={rotationY} rotation-x={-0.14}>
      <group ref={root} />
    </group>
  )
}

/** Regal set dressing behind VITE_LIBRARY_PROPS=1: chandeliers + library ladder. */
export default function LibraryProps() {
  return (
    <>
      <Chandelier position={[-3.6, 4.3, 0.4]} />
      <Chandelier position={[3.6, 4.3, 0.4]} />
      <LibraryLadder position={[1.7, 0, -0.75]} rotationY={0.18} />
    </>
  )
}
