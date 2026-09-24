import { useEffect, useMemo, useRef, type RefObject } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import BookInstances from './BookInstances'
import { SPHERE_RADIUS, sphereBooks } from './sphere'

/** One revolution about this many seconds — ambient, not a spinning globe. */
const REVOLUTION_SECONDS = 70

interface BookSphereProps {
  /** Course is open: sphere eases left and shrinks. */
  docked: boolean
  night: boolean
  /** Click without a drag, used to close the open course. */
  onIdleClick?: () => void
  /** World-space point on the sphere's right edge, updated every frame. */
  exitPoint?: RefObject<THREE.Vector3 | null>
}

function useRadialTexture() {
  return useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 256
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    const grad = ctx.createRadialGradient(128, 128, 8, 128, 128, 128)
    grad.addColorStop(0, 'rgba(90, 75, 60, 0.55)')
    grad.addColorStop(1, 'rgba(90, 75, 60, 0)')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, 256, 256)
    const tex = new THREE.CanvasTexture(canvas)
    tex.colorSpace = THREE.SRGBColorSpace
    return tex
  }, [])
}

/**
 * A globe of books. Spins on its axis, and can be dragged.
 * While a course is open it sits smaller on the left.
 */
export default function BookSphere({ docked, night, onIdleClick, exitPoint }: BookSphereProps) {
  const rig = useRef<THREE.Group>(null)
  const spin = useRef<THREE.Group>(null)
  const yaw = useRef(0.4)
  const slide = useRef(0)
  const scale = useRef(1)
  const dragging = useRef(false)
  const dockedRef = useRef(docked)
  const clickRef = useRef(onIdleClick)
  dockedRef.current = docked
  clickRef.current = onIdleClick

  const books = useMemo(() => sphereBooks(), [])
  const shadowMap = useRadialTexture()
  const { gl } = useThree()

  useEffect(() => {
    const el = gl.domElement
    const drag = { active: false, moved: false, x: 0 }

    const onDown = (event: PointerEvent) => {
      if (event.button !== 0) return
      drag.active = true
      drag.moved = false
      drag.x = event.clientX
      dragging.current = true
    }
    const onMove = (event: PointerEvent) => {
      if (!drag.active) return
      const dx = event.clientX - drag.x
      if (Math.abs(dx) > 3) drag.moved = true
      drag.x = event.clientX
      if (drag.moved) yaw.current += dx * 0.006
    }
    const onUp = () => {
      if (drag.active && !drag.moved) clickRef.current?.()
      drag.active = false
      dragging.current = false
    }

    el.addEventListener('pointerdown', onDown)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      el.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [gl])

  useFrame((_, dt) => {
    if (!rig.current || !spin.current) return
    if (!dragging.current) yaw.current += dt * ((Math.PI * 2) / REVOLUTION_SECONDS)
    spin.current.rotation.y = yaw.current

    const targetX = dockedRef.current ? -3.15 : 0
    const targetScale = dockedRef.current ? 0.46 : 1
    slide.current = THREE.MathUtils.damp(slide.current, targetX, 2.6, dt)
    scale.current = THREE.MathUtils.damp(scale.current, targetScale, 2.6, dt)
    rig.current.position.set(slide.current, 0.28, 0)
    rig.current.scale.setScalar(scale.current)
    if (exitPoint?.current) {
      exitPoint.current.set(
        slide.current + SPHERE_RADIUS * scale.current * 0.86,
        0.42,
        0.35 * scale.current,
      )
    }
  })

  return (
    <group ref={rig}>
      <group rotation={[0.1, 0, 0]}>
        {/* Matches the page color so gaps stay quiet and the far side stays hidden. */}
        <mesh>
          <sphereGeometry args={[1.96, 48, 32]} />
          <meshBasicMaterial color={night ? '#1c1916' : '#e7e0d6'} toneMapped={false} />
        </mesh>
        <group ref={spin}>
          <BookInstances books={books} />
        </group>
      </group>

      {shadowMap && (
        <mesh position={[0, -2.45, 0]} rotation-x={-Math.PI / 2}>
          <planeGeometry args={[5.2, 1.7]} />
          <meshBasicMaterial map={shadowMap} transparent depthWrite={false} />
        </mesh>
      )}
    </group>
  )
}
