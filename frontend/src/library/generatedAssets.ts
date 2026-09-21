/**
 * Flip on a Tripo/Meshy keeper without shipping it by default.
 * Copy the GLB to /models/hero-bookshelf.glb and start Vite with
 * VITE_GENERATED_BOOKCASE=1. Production stays procedural until a keeper is
 * reviewed, compressed, and this flag is set in the host environment.
 */
export const GENERATED_BOOKCASE_URL: string | null =
  import.meta.env.VITE_GENERATED_BOOKCASE === '1' ? '/models/hero-bookshelf.glb' : null

/**
 * Regal set dressing (Meshy previews / Tripo web-app keepers), same contract:
 * compressed GLBs live in /models/, gitignored, gated by VITE_LIBRARY_PROPS=1.
 */
export const LIBRARY_PROPS_ENABLED: boolean = import.meta.env.VITE_LIBRARY_PROPS === '1'

export const PROP_URLS = {
  chandelier: '/models/prop-chandelier.glb',
  ladder: '/models/prop-ladder.glb',
} as const
