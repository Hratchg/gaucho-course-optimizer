/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_GENERATED_BOOKCASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
