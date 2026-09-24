#!/usr/bin/env bash
# Usage: setup_runs.sh <iteration-dir>
# Builds an isolated git repo per eval x config: <iter>/<eval-name>/<config>/run-1/repo
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
iter="$1"
python3 - "$here" "$iter" <<'PY'
import json, os, shutil, subprocess, sys
here, it = sys.argv[1], sys.argv[2]
for e in json.load(open(f"{here}/evals.json"))["evals"]:
    for cfg in ("with_skill", "without_skill"):
        run = f"{it}/eval-{e['id']}-{e['name']}/{cfg}/run-1"
        repo = f"{run}/repo"
        shutil.rmtree(run, ignore_errors=True)
        shutil.copytree(f"{here}/fixtures/project", repo)
        if e["setup"] == "project+collision":
            shutil.copy(f"{here}/fixtures/project-collision-existing.md",
                        f"{repo}/docs/decisions/2026-09-24-rate-limiting-public-api.md")
        if e["setup"] == "project-without-decisions":
            shutil.rmtree(f"{repo}/docs")
        os.makedirs(f"{run}/outputs")
        g = lambda *a: subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True)
        g("init", "-q"); g("add", "-A")
        g("-c", "user.name=eval", "-c", "user.email=eval@example.com", "commit", "-qm", "init")
        meta = {"eval_id": e["id"], "eval_name": e["name"], "prompt": e["prompt"], "assertions": e["assertions"]}
        json.dump(meta, open(f"{it}/eval-{e['id']}-{e['name']}/eval_metadata.json", "w"), indent=2, ensure_ascii=False)
PY
