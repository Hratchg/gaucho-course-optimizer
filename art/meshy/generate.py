#!/usr/bin/env python3
"""Meshy text-to-3D generation for CoursePick, with credit ledger.

Reads the API key from art/meshy/.env (never the shell environment) so this
repo's generations are always attributable to the CoursePick pipeline.

Default is preview (mesh only). Pass --refine to texture a finished preview.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
API = "https://api.meshy.ai"


def load_key() -> str:
    env = HERE / ".env"
    if not env.exists():
        sys.exit(
            "art/meshy/.env not found. Create it with MESHY_API_KEY=msy_... "
            "(https://www.meshy.ai/settings/api). Do not reuse the Tripo key."
        )
    for line in env.read_text().splitlines():
        if line.startswith("MESHY_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    sys.exit("MESHY_API_KEY not found in art/meshy/.env")


def request(key: str, method: str, path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"Meshy HTTP {exc.code} on {path}: {raw}")


def balance(key: str) -> int | float:
    data = request(key, "GET", "/openapi/v1/balance")
    return data.get("balance", 0)


def poll(key: str, task_id: str) -> dict:
    while True:
        time.sleep(8)
        task = request(key, "GET", f"/openapi/v2/text-to-3d/{task_id}")
        status = task.get("status", "UNKNOWN")
        prog = task.get("progress", 0)
        print(f"  {status} {prog}%")
        if status == "SUCCEEDED":
            return task
        if status in ("FAILED", "CANCELED"):
            sys.exit(f"task ended: {status}: {task}")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    print(f"saved: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def append_ledger(row: dict) -> None:
    with (HERE / "ledger.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--name", help="output file stem, e.g. hero-bookshelf")
    ap.add_argument("--refine", action="store_true", help="also run the texturing refine pass")
    ap.add_argument("--preview-task", help="skip preview; refine this existing Meshy task id")
    ap.add_argument("--balance", action="store_true", help="print credits and exit")
    ap.add_argument("--dry-run", action="store_true", help="check key + balance, do not create a task")
    args = ap.parse_args()

    key = load_key()
    before = balance(key)
    print(f"credits: {before}")
    if args.balance:
        return
    if args.dry_run:
        print("dry-run: no task created")
        return
    if not args.name:
        sys.exit("--name is required (unless --balance / --dry-run)")
    if not args.prompt and not args.preview_task:
        sys.exit("prompt is required unless --preview-task is set")

    preview_id = args.preview_task
    if not preview_id:
        created = request(key, "POST", "/openapi/v2/text-to-3d", {
            "mode": "preview",
            "prompt": args.prompt,
            "ai_model": "latest",
            "should_remesh": True,
            "target_formats": ["glb"],
        })
        preview_id = created.get("result")
        print(f"preview task: {preview_id}")
        preview = poll(key, preview_id)
    else:
        print(f"using preview task: {preview_id}")
        preview = request(key, "GET", f"/openapi/v2/text-to-3d/{preview_id}")

    models = (preview.get("model_urls") or {})
    preview_url = models.get("glb")
    if preview_url:
        download(preview_url, HERE / "outputs" / f"{args.name}-preview.glb")

    refine_id = None
    if args.refine:
        created = request(key, "POST", "/openapi/v2/text-to-3d", {
            "mode": "refine",
            "preview_task_id": preview_id,
            "enable_pbr": True,
            "target_formats": ["glb"],
        })
        refine_id = created.get("result")
        print(f"refine task: {refine_id}")
        refined = poll(key, refine_id)
        refine_url = (refined.get("model_urls") or {}).get("glb")
        if not refine_url:
            sys.exit(f"refine succeeded but no glb url: {refined}")
        download(refine_url, HERE / "outputs" / f"{args.name}.glb")

    after = balance(key)
    print(f"credits after: {after} (spent {before - after})")
    append_ledger({
        "ts": datetime.now(timezone.utc).isoformat(),
        "project": "coursepick",
        "provider": "meshy",
        "preview_task_id": preview_id,
        "refine_task_id": refine_id,
        "prompt": args.prompt,
        "refine": args.refine,
        "credits_before": before,
        "credits_after": after,
        "output": f"art/meshy/outputs/{args.name}.glb" if args.refine else f"art/meshy/outputs/{args.name}-preview.glb",
    })


if __name__ == "__main__":
    main()
