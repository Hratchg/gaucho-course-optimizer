# Meshy asset pipeline — CoursePick

Dedicated Meshy 3D generation pipeline for this repo. Same isolation rules as
`art/tripo/`: repo-local key, own outputs, own ledger.

- **Key:** `art/meshy/.env` (`MESHY_API_KEY=msy_...`) from
  https://www.meshy.ai/settings/api. Do not put the Tripo key here.
- **Ledger:** `ledger.jsonl` records preview/refine task IDs and credits
  before/after.
- **Outputs:** `outputs/` (gitignored). Preview meshes are
  `{name}-preview.glb`; refined keepers are `{name}.glb`.

Meshy is a two-step workflow: preview the silhouette, then refine (texture)
only if the shape is worth keeping.

## Usage

```sh
python3 art/meshy/generate.py --balance
python3 art/meshy/generate.py "a wooden library bookshelf, ..." --name hero-bookshelf
python3 art/meshy/generate.py "..." --name hero-bookshelf --refine
python3 art/meshy/generate.py --name hero-bookshelf --preview-task <id> --refine
```
