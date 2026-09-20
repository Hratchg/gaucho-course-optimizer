import { Suspense, useMemo } from 'react'
import * as THREE from 'three'
import { Canvas } from '@react-three/fiber'
import { Environment, ContactShadows, useTexture } from '@react-three/drei'
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing'
import Bookcase from './Bookcase'
import GeneratedBookcase from './GeneratedBookcase'
import PulledBook from './PulledBook'
import CameraRig, { type CameraTarget } from './CameraRig'
import { BOOKCASES } from './layout'
import { GENERATED_BOOKCASE_URL } from './generatedAssets'

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
      camera={{ position: [0, 2.35, 9.3], fov: 48 }}
      gl={{ antialias: true }}
      aria-hidden
    >
      <color attach="background" args={[night ? '#171428' : '#2c2545']} />
      <fog attach="fog" args={[night ? '#171428' : '#2c2545', 16, 34]} />

      <Suspense fallback={null}>
        <Environment files="/3d/library-hdri.hdr" environmentIntensity={night ? 0.4 : 0.55} />

        {/* Key light — warm reading lamps feel */}
        <directionalLight
          position={[2, 7, 6]}
          intensity={night ? 1.05 : 1.45}
          color={night ? '#ffd9a0' : '#fff2dd'}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <hemisphereLight
          args={[night ? '#4a3f72' : '#7a7098', night ? '#1a1528' : '#3a3048', night ? 0.42 : 0.28]}
        />
        <ambientLight intensity={night ? 0.28 : 0.3} color="#cbb8ff" />
        {/* Warm accent pools per bookcase — sit in front of each plaque */}
        {BOOKCASES.map((b) => (
          <pointLight
            key={b.dept}
            position={[b.position[0], 3.35, b.position[2] + 1.35]}
            intensity={night ? 2.4 : 1.25}
            distance={6.8}
            color="#ffc93c"
          />
        ))}

        <Floor />
        <BackWall night={night} />
        {BOOKCASES.map((b, i) =>
          GENERATED_BOOKCASE_URL ? (
            <GeneratedBookcase key={b.dept} url={GENERATED_BOOKCASE_URL} slot={b} seed={i * 7919 + 13} />
          ) : (
            <Bookcase key={b.dept} slot={b} seed={i * 7919 + 13} />
          ),
        )}

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
          <Bloom intensity={night ? 0.38 : 0.22} luminanceThreshold={0.82} mipmapBlur />
          <Vignette eskil={false} offset={0.22} darkness={night ? 0.5 : 0.62} />
        </EffectComposer>
      </Suspense>
    </Canvas>
  )
}
