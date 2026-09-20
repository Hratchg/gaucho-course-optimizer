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

## Usage

```sh
python art/tripo/generate.py "a wooden library bookshelf, ..." --name hero-bookshelf
```
