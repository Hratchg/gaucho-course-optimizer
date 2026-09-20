#!/usr/bin/env python3
"""Tripo text-to-model generation for CoursePick, with credit ledger.

Reads the API key from art/tripo/.env (never the shell environment) so this
repo's generations are always attributable to the CoursePick pipeline.
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
API = "https://api.tripo3d.ai/v2/openapi"


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
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if body.get("code") != 0:
        sys.exit(f"Tripo API error on {path}: {body}")
    return body["data"]


def balance(key: str) -> int:
    return call(key, "/user/balance")["balance"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--name", required=True, help="output file stem, e.g. hero-bookshelf")
    ap.add_argument("--texture", default="standard", choices=["no", "standard", "HD"])
    args = ap.parse_args()

    key = load_key()
    before = balance(key)
    print(f"credits before: {before}")

    task = call(key, "/task", {
        "type": "text_to_model",
        "prompt": args.prompt,
        "texture": args.texture != "no",
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
            model_url = st["output"].get("pbr_model") or st["output"].get("model")
            break
        if status in ("failed", "cancelled", "banned"):
            sys.exit(f"task ended: {status}: {st}")

    out = HERE / "outputs" / f"{args.name}.glb"
    out.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(model_url, out)
    after = balance(key)
    print(f"saved: {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print(f"credits after: {after} (spent {before - after})")

    with (HERE / "ledger.jsonl").open("a") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "project": "coursepick",
            "task_id": task_id,
            "prompt": args.prompt,
            "texture": args.texture,
            "credits_before": before,
            "credits_after": after,
            "output": str(out.relative_to(HERE.parent.parent)),
        }) + "\n")


if __name__ == "__main__":
    main()
