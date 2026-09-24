import { Suspense, useRef, useState } from 'react'
import * as THREE from 'three'
import { Canvas, useThree } from '@react-three/fiber'
import { useLayoutEffect } from 'react'
import BookSphere from './BookSphere'
import PulledBook, { type BorrowedBook } from './PulledBook'

function Backdrop() {
  const { scene, gl } = useThree()
  useLayoutEffect(() => {
    scene.background = null
    gl.setClearColor(0x000000, 0)
  }, [gl, scene])
  return null
}

export interface SphereFlight {
  direction: 'out' | 'back'
  /** Changes when a new book is lifted out of the sphere. */
  claimKey: number
}

export interface LibrarySceneProps {
  /** Sphere shifts left while a course is open or a book is in flight. */
  docked: boolean
  /** One sphere book in motion. Null once the course panel is open. */
  flight: SphereFlight | null
  /** Keep that book out of the sphere while its course is on screen. */
  holdBook: boolean
  night: boolean
  onSphereClick?: () => void
}

/**
 * Rotating sphere of books. Searching a course lifts one of those books
 * toward the panel. A later search flies it back before lifting another.
 */
export default function LibraryScene({ docked, flight, holdBook, night, onSphereClick }: LibrarySceneProps) {
  const slot = useRef<THREE.Vector3 | null>(new THREE.Vector3())
  const [look, setLook] = useState<BorrowedBook | null>(null)

  return (
    <Canvas
      dpr={[1, 1.5]}
      camera={{ position: [0, 0.28, 9.1], fov: 34 }}
      gl={{ antialias: true, alpha: true }}
      style={{ touchAction: 'none' }}
      aria-hidden
    >
      <Backdrop />
      <hemisphereLight args={[night ? '#3a342c' : '#f4efe6', night ? '#14110e' : '#c4b5a4', night ? 0.45 : 0.65]} />
      <ambientLight intensity={night ? 0.35 : 0.42} color={night ? '#d9cbb8' : '#fff6ea'} />
      <directionalLight
        position={[3.2, 4.8, 5.4]}
        intensity={night ? 1.15 : 1.55}
        color={night ? '#ffe4c4' : '#fff8ee'}
      />

      <Suspense fallback={null}>
        <BookSphere
          docked={docked}
          night={night}
          onIdleClick={onSphereClick}
          holdBook={holdBook}
          claimKey={flight?.direction === 'out' ? flight.claimKey : 0}
          onClaim={setLook}
          slot={slot}
        />
        {flight && look && (flight.direction === 'back' || look.claimKey === flight.claimKey) && (
          <PulledBook
            key={`${flight.direction}-${flight.claimKey}`}
            direction={flight.direction}
            claimKey={flight.claimKey}
            look={look}
            slot={slot}
          />
        )}
      </Suspense>
    </Canvas>
  )
}
