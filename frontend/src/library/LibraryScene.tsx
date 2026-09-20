import { Suspense, useMemo } from 'react'
import * as THREE from 'three'
import { Canvas } from '@react-three/fiber'
import { Environment, ContactShadows, useTexture } from '@react-three/drei'
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing'
import Bookcase from './Bookcase'
import PulledBook from './PulledBook'
import CameraRig, { type CameraTarget } from './CameraRig'
import { BOOKCASES } from './layout'

export interface LibrarySceneProps {
  target: CameraTarget
  pulledCourse: { code: string; title?: string; dept: string } | null
  night: boolean
}

function Floor() {
  const [woodMap, woodRough] = useTexture(['/3d/wood-diff.jpg', '/3d/wood-rough.jpg'])
  const map = useMemo(() => {
    const m = woodMap.clone()
    m.wrapS = m.wrapT = THREE.RepeatWrapping
    m.repeat.set(8, 8)
    m.colorSpace = THREE.SRGBColorSpace
    return m
  }, [woodMap])
  const rough = useMemo(() => {
    const m = woodRough.clone()
    m.wrapS = m.wrapT = THREE.RepeatWrapping
    m.repeat.set(8, 8)
    return m
  }, [woodRough])
  return (
    <mesh rotation-x={-Math.PI / 2} position={[0, 0, 1]} receiveShadow>
      <planeGeometry args={[40, 24]} />
      <meshStandardMaterial map={map} roughnessMap={rough} roughness={0.9} color="#9a7b57" />
    </mesh>
  )
}

function BackWall({ night }: { night: boolean }) {
  return (
    <mesh position={[0, 4, -3.2]}>
      <planeGeometry args={[44, 12]} />
      <meshStandardMaterial color={night ? '#241f38' : '#4a3f63'} roughness={1} />
    </mesh>
  )
}

/**
 * The 3D library. Pure presentational: camera target + pulled book come
 * from the parent (LibraryLanding) which owns search state.
 */
export default function LibraryScene({ target, pulledCourse, night }: LibrarySceneProps) {
  return (
    <Canvas
      shadows
      dpr={[1, 1.75]}
      camera={{ position: [0, 2.1, 5.6], fov: 42 }}
      gl={{ antialias: true }}
      aria-hidden
    >
      <color attach="background" args={[night ? '#171428' : '#2c2545']} />
      <fog attach="fog" args={[night ? '#171428' : '#2c2545', 9, 22]} />

      <Suspense fallback={null}>
        <Environment files="/3d/library-hdri.hdr" environmentIntensity={night ? 0.25 : 0.55} />

        {/* Key light — warm reading lamps feel */}
        <directionalLight
          position={[3, 6, 4]}
          intensity={night ? 0.7 : 1.4}
          color={night ? '#ffd9a0' : '#fff2dd'}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <ambientLight intensity={night ? 0.12 : 0.25} color="#cbb8ff" />
        {/* Warm accent pools per bookcase */}
        {BOOKCASES.map((b) => (
          <pointLight
            key={b.dept}
            position={[b.position[0], 3.4, b.position[2] + 1.2]}
            intensity={night ? 1.6 : 0.8}
            distance={5.5}
            color="#ffc93c"
          />
        ))}

        <Floor />
        <BackWall night={night} />
        {BOOKCASES.map((b, i) => (
          <Bookcase key={b.dept} slot={b} seed={i * 7919 + 13} />
        ))}

        {pulledCourse && (
          <PulledBook
            courseCode={pulledCourse.code}
            courseTitle={pulledCourse.title}
            dept={pulledCourse.dept}
            active
          />
        )}

        <ContactShadows position={[0, 0.01, 0]} opacity={0.55} scale={26} blur={2.4} far={4} />
        <CameraRig target={target} />

        <EffectComposer>
          <Bloom intensity={night ? 0.55 : 0.25} luminanceThreshold={0.8} mipmapBlur />
          <Vignette eskil={false} offset={0.18} darkness={0.75} />
        </EffectComposer>
      </Suspense>
    </Canvas>
  )
}
