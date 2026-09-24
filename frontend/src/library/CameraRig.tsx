import { useRef } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'

export interface CameraTarget {
  /** extra push-in when a book is pulled */
  bookFocus: boolean
  /** final dive into the pulled book before navigating to the course page */
  flyIn?: boolean
}

const REST_POS = new THREE.Vector3(0, 2.12, 5.55)
const REST_LOOK = new THREE.Vector3(0, 2.02, 0)
const FOCUS_POS = new THREE.Vector3(0.15, 1.88, 3.7)
const FOCUS_LOOK = new THREE.Vector3(0.2, 1.95, 0.55)
const FLY_POS = new THREE.Vector3(0.05, 1.58, 2.15)
const FLY_LOOK = new THREE.Vector3(0.08, 1.72, 0.95)

/** Smoothly flies the camera from the filled-shelf rest shot into the pulled book. */
export default function CameraRig({ target }: { target: CameraTarget }) {
  const { camera } = useThree()
  const look = useRef(REST_LOOK.clone())
  const desiredPos = useRef(REST_POS.clone())
  const desiredLook = useRef(REST_LOOK.clone())

  useFrame((state, dt) => {
    if (target.flyIn) {
      desiredPos.current.copy(FLY_POS)
      desiredLook.current.copy(FLY_LOOK)
    } else if (target.bookFocus) {
      desiredPos.current.copy(FOCUS_POS)
      desiredLook.current.copy(FOCUS_LOOK)
    } else {
      const t = state.clock.elapsedTime
      desiredPos.current.set(
        REST_POS.x + Math.sin(t * 0.18) * 0.06,
        REST_POS.y + Math.sin(t * 0.13) * 0.025,
        REST_POS.z,
      )
      desiredLook.current.copy(REST_LOOK)
    }

    const lambda = target.flyIn ? 3.4 : 2.2
    camera.position.x = THREE.MathUtils.damp(camera.position.x, desiredPos.current.x, lambda, dt)
    camera.position.y = THREE.MathUtils.damp(camera.position.y, desiredPos.current.y, lambda, dt)
    camera.position.z = THREE.MathUtils.damp(camera.position.z, desiredPos.current.z, lambda, dt)
    look.current.x = THREE.MathUtils.damp(look.current.x, desiredLook.current.x, lambda, dt)
    look.current.y = THREE.MathUtils.damp(look.current.y, desiredLook.current.y, lambda, dt)
    look.current.z = THREE.MathUtils.damp(look.current.z, desiredLook.current.z, lambda, dt)
    camera.lookAt(look.current)
  })

  return null
}
