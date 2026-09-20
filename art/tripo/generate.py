#!/usr/bin/env python3
"""Tripo text-to-model generation for CoursePick, with credit ledger.

Reads the API key from art/tripo/.env (never the shell environment) so this
repo's generations are always attributable to the CoursePick pipeline.

Cost (H3 text_to_model): no texture = 10, standard = 20, HD/detailed = 30.
`pbr` must be false when texture is off — otherwise Tripo forces texturing
and the 10-credit draft becomes a 20-credit task.
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
API = "https://api.tripo3d.ai/v2/openapi"

# H3 text_to_model list prices. Keep in sync with
# https://docs.tripo3d.ai/get-started/pricing.html
COST = {"no": 10, "standard": 20, "HD": 30}


def load_key() -> str:
    env = HERE / ".env"
    if not env.exists():
        sys.exit("art/tripo/.env not found. Create it with TRIPO3D_API_KEY=...")
    for line in env.read_text().splitlines():
        if line.startswith("TRIPO3D_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("TRIPO3D_API_KEY not found in art/tripo/.env")


def call(key: str, path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"Tripo HTTP {exc.code} on {path}: {raw}")
    if body.get("code") != 0:
        sys.exit(f"Tripo API error on {path}: {body}")
    return body["data"]


def balance(key: str) -> int:
    data = call(key, "/user/balance")
    return int(data.get("balance", 0))


def append_ledger(row: dict) -> None:
    with (HERE / "ledger.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--name", help="output file stem, e.g. hero-bookshelf")
    ap.add_argument("--texture", default="no", choices=["no", "standard", "HD"])
    ap.add_argument("--balance", action="store_true", help="print credits and exit")
    ap.add_argument("--dry-run", action="store_true", help="print cost vs balance, do not create a task")
    args = ap.parse_args()

    key = load_key()
    before = balance(key)
    print(f"credits: {before}")
    if args.balance:
        return

    if not args.prompt or not args.name:
        sys.exit("prompt and --name are required (unless --balance)")

    estimate = COST[args.texture]
    print(f"estimated cost: {estimate} ({args.texture} texture)")
    if before < estimate:
        sys.exit(
            f"not enough credits: need {estimate}, have {before}. "
            "Top up at https://www.tripo3d.ai or use --texture no (10 credits)."
        )
    if args.dry_run:
        print("dry-run: no task created")
        return

    textured = args.texture != "no"
    task = call(key, "/task", {
        "type": "text_to_model",
        "prompt": args.prompt,
        "texture": textured,
        # pbr=true silently re-enables texture and doubles the cost.
        "pbr": textured,
        "texture_quality": "detailed" if args.texture == "HD" else "standard",
    })
    task_id = task["task_id"]
    print(f"task: {task_id}")

    model_url = None
    while True:
        time.sleep(10)
        st = call(key, f"/task/{task_id}")
        status, prog = st["status"], st.get("progress", 0)
        print(f"  {status} {prog}%")
        if status == "success":
            out = st.get("output") or {}
            model_url = (
                out.get("pbr_model")
                or out.get("model")
                or out.get("model_url")
                or out.get("base_model")
            )
            break
        if status in ("failed", "cancelled", "banned"):
            sys.exit(f"task ended: {status}: {st}")

    dest = HERE / "outputs" / f"{args.name}.glb"
    dest.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(model_url, dest)
    after = balance(key)
    print(f"saved: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    print(f"credits after: {after} (spent {before - after})")

    append_ledger({
        "ts": datetime.now(timezone.utc).isoformat(),
        "project": "coursepick",
        "provider": "tripo",
        "task_id": task_id,
        "prompt": args.prompt,
        "texture": args.texture,
        "credits_before": before,
        "credits_after": after,
        "output": str(dest.relative_to(HERE.parent.parent)),
    })


if __name__ == "__main__":
    main()
