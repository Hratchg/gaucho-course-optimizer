# CoursePick generated-asset pipelines

Two isolated pipelines so Needle and CoursePick never share an env file or
output folder. Credits still live on the **account**, so the only hard
firewall is a separate provider account. The ledger is how we attribute spend.

| Provider | Folder | Key file | Ledger |
| --- | --- | --- | --- |
| Tripo | `art/tripo/` | `art/tripo/.env` (`TRIPO3D_API_KEY`) | `art/tripo/ledger.jsonl` |
| Meshy | `art/meshy/` | `art/meshy/.env` (`MESHY_API_KEY`) | `art/meshy/ledger.jsonl` |

Keys, raw GLBs, and ledgers-with-secrets stay out of git (see `.gitignore`).
Compressed keepers that ship go in `frontend/public/models/` and are flipped
on with `VITE_GENERATED_BOOKCASE=1`.

## First asset: hero bookshelf

Empty-shelf university oak case. One mesh, instanced six times in the landing
scene, with the procedural brass plaque still drawn in Three.

```sh
# Tripo — 10 credits untextured, 20 standard, 30 HD
python3 art/tripo/generate.py --balance
python3 art/tripo/generate.py --dry-run \
  "A tall university-library oak bookcase, empty shelves, brass fittings, photoreal, game-ready" \
  --name hero-bookshelf --texture no

# Meshy — preview first, refine only if the silhouette is right
python3 art/meshy/generate.py --balance
python3 art/meshy/generate.py \
  "A tall university-library oak bookcase, empty shelves, brass fittings, photoreal, game-ready" \
  --name hero-bookshelf
```

Then copy the keeper to `frontend/public/models/hero-bookshelf.glb` and run
the frontend with `VITE_GENERATED_BOOKCASE=1`.
