#!/usr/bin/env bash
# Compress the Max-textured keeper for the local Vite preview.
# Does not call Tripo/Meshy. Source GLB stays in outputs/; the web copy is
# gitignored. Quantize (not Draco/Meshopt) so three.js loads it with no decoder.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
src="$root/art/tripo/outputs/hero-bookshelf-web.glb"
dst="$root/frontend/public/models/hero-bookshelf.glb"
cli=(npx --yes @gltf-transform/cli@4.2.1)

if [[ ! -f "$src" ]]; then
  echo "missing $src" >&2
  exit 1
fi

mkdir -p "$(dirname "$dst")"
"${cli[@]}" optimize "$src" "$dst" \
  --compress quantize \
  --texture-compress webp \
  --texture-size 1024 \
  --simplify true \
  --simplify-ratio 0.12 \
  --simplify-error 0.0008 \
  --weld true

ls -lh "$src" "$dst"
