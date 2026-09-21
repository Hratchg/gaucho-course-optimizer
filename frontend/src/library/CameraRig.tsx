import { useRef } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { slotForDept } from './layout'

export interface CameraTarget {
  /** null → resting overview shot of the whole aisle */
  dept: string | null
  /** extra push-in when a book is pulled */
  bookFocus: boolean
  /** final dive into the pulled book before navigating to the book view */
  flyIn?: boolean
}

const REST_POS = new THREE.Vector3(0, 2.35, 9.3)
const REST_LOOK = new THREE.Vector3(0, 1.45, -1.0)

/** Smoothly flies the camera between the overview and a focused bookcase. */
export default function CameraRig({ target }: { target: CameraTarget }) {
  const { camera } = useThree()
  const look = useRef(REST_LOOK.clone())
  const desiredPos = useRef(REST_POS.clone())
  const desiredLook = useRef(REST_LOOK.clone())

  useFrame((_, dt) => {
    if (target.dept) {
      const slot = slotForDept(target.dept)
      const push = target.flyIn ? 1.1 : target.bookFocus ? 2.6 : 2.9
      desiredPos.current.set(
        slot.position[0] + Math.sin(slot.rotationY) * push,
        target.bookFocus ? 1.8 : 1.9,
        slot.position[2] + Math.cos(slot.rotationY) * push,
      )
      desiredLook.current.set(
        slot.position[0] + (target.bookFocus ? 0.45 : 0),
        target.bookFocus ? 1.7 : 1.6,
        slot.position[2] + (target.bookFocus ? 0.4 : 0),
      )
    } else {
      desiredPos.current.copy(REST_POS)
      desiredLook.current.copy(REST_LOOK)
    }

    const lambda = 2.2
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
