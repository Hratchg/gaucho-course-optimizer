import { Suspense, useLayoutEffect, useRef } from 'react'
import * as THREE from 'three'
import { Canvas, useThree } from '@react-three/fiber'
import BookSphere from './BookSphere'
import PulledBook from './PulledBook'

function Backdrop({ night }: { night: boolean }) {
  const { scene } = useThree()
  useLayoutEffect(() => {
    scene.background = new THREE.Color(night ? '#1c1916' : '#efeae3')
  }, [night, scene])
  return null
}

export interface LibrarySceneProps {
  /** Sphere shifts left while a course is open or a book is in flight. */
  docked: boolean
  pulledCourse: { code: string; title?: string; dept: string; key?: number } | null
  night: boolean
  onSphereClick?: () => void
}

/**
 * Rotating sphere of books. Searching a course docks the sphere on the left
 * and flies one book toward the course panel on the right.
 */
export default function LibraryScene({ docked, pulledCourse, night, onSphereClick }: LibrarySceneProps) {
  const exitPoint = useRef(new THREE.Vector3(1.55, 0.15, 0.6))
  return (
    <Canvas
      dpr={[1, 1.5]}
      camera={{ position: [0, 0.28, 9.1], fov: 34 }}
      gl={{ antialias: true }}
      style={{ touchAction: 'none' }}
      aria-hidden
    >
      <Backdrop night={night} />
      <hemisphereLight args={[night ? '#3a342c' : '#f4efe6', night ? '#14110e' : '#c4b5a4', night ? 0.45 : 0.65]} />
      <ambientLight intensity={night ? 0.35 : 0.42} color={night ? '#d9cbb8' : '#fff6ea'} />
      <directionalLight
        position={[3.2, 4.8, 5.4]}
        intensity={night ? 1.15 : 1.55}
        color={night ? '#ffe4c4' : '#fff8ee'}
      />

      <Suspense fallback={null}>
        <BookSphere docked={docked} night={night} onIdleClick={onSphereClick} exitPoint={exitPoint} />
        {pulledCourse && (
          <PulledBook
            key={pulledCourse.key ?? pulledCourse.code}
            courseCode={pulledCourse.code}
            courseTitle={pulledCourse.title}
            dept={pulledCourse.dept}
            active
            exitPoint={exitPoint}
          />
        )}
      </Suspense>
    </Canvas>
  )
}
