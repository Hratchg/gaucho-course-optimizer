#!/usr/bin/env bash
# Compress Meshy prop previews for the local Vite demo (same pattern as
# art/tripo/compress.sh). No API calls. Web copies are gitignored.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
cli=(npx --yes @gltf-transform/cli@4.2.1)

for name in prop-chandelier prop-ladder; do
  src="$root/art/meshy/outputs/${name}-preview.glb"
  dst="$root/frontend/public/models/${name}.glb"
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
    --simplify-ratio 0.35 \
    --simplify-error 0.001 \
    --weld true
  ls -lh "$src" "$dst"
done
