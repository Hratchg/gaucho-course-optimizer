import { useMemo } from 'react'
import type * as THREE from 'three'
import {
  applyBookInstances,
  getSpineMaterials,
  groupBooksByVariant,
  useBookGeometry,
  type BookInstance,
} from './books'

/**
 * Renders packed books as one InstancedMesh per spine variant so every book
 * gets a realistic spine texture (cloth sides, page-edge top, gilt spine)
 * while staying instanced. ~10 draw calls per bookcase.
 */
export default function BookInstances({ books }: { books: BookInstance[] }) {
  const geo = useBookGeometry()
  const materials = useMemo(() => getSpineMaterials(), [])
  const groups = useMemo(() => [...groupBooksByVariant(books).entries()], [books])

  return (
    <>
      {groups.map(([variant, list]) => (
        <instancedMesh
          key={variant}
          ref={(mesh) => applyBookInstances(mesh, list)}
          args={[geo, materials[variant] as unknown as THREE.Material, list.length]}
          castShadow
        />
      ))}
    </>
  )
}
