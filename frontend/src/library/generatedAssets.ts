/**
 * Flip on a Tripo/Meshy keeper without shipping it by default.
 * Copy the GLB to /models/hero-bookshelf.glb and start Vite with
 * VITE_GENERATED_BOOKCASE=1. Production stays procedural until a keeper is
 * reviewed, compressed, and this flag is set in the host environment.
 */
export const GENERATED_BOOKCASE_URL: string | null =
  import.meta.env.VITE_GENERATED_BOOKCASE === '1' ? '/models/hero-bookshelf.glb' : null
