# Tripo asset pipeline — CoursePick

Dedicated Tripo 3D generation pipeline for this repo, kept separate from other
projects (e.g. Needle) for credit attribution.

- **Key:** read from `art/tripo/.env` (`TRIPO3D_API_KEY=...`), *not* from the
  shell environment, so this repo always uses the key you intend for CoursePick.
  If you later create a separate Tripo account for CoursePick, just change the
  key in that one file.
- **Ledger:** every generation appends a line to `ledger.jsonl` with the UTC
  timestamp, prompt, task ID, and the account credit balance before/after, so
  you can always tell which credits CoursePick consumed.
- **Outputs:** models land in `outputs/` (gitignored; large binaries). Final
  compressed assets that ship are copied to `frontend/public/models/`.
- **Compress:** `art/tripo/compress.sh` takes the Max-textured keeper
  (`outputs/hero-bookshelf-web.glb`) down to ~1 MB (quantize + WebP 1K,
  no Draco) at `frontend/public/models/hero-bookshelf.glb`. Preview with
  `VITE_GENERATED_BOOKCASE=1`; do not commit the GLB.

## Cost (H3 `text_to_model`)

| Flag | Credits | Notes |
| --- | --- | --- |
| `--texture no` (default) | 10 | Also sends `pbr: false`. Required — `pbr: true` forces texturing. |
| `--texture standard` | 20 | |
| `--texture HD` | 30 | `texture_quality=detailed` |

The previous CoursePick attempt failed at 15 credits because the script left
`pbr` at the API default (`true`), which silently billed a 20-credit textured
task. That is fixed.

## Usage

```sh
python3 art/tripo/generate.py --balance
python3 art/tripo/generate.py "a wooden library bookshelf, ..." --name hero-bookshelf
python3 art/tripo/generate.py "..." --name hero-bookshelf --texture standard
```
