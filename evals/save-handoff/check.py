#!/usr/bin/env python3
"""Grade every run of one save-handoff iteration.

Usage: python3 evals/save-handoff/check.py evals/save-handoff/workspace/iteration-N

Each run folder was built by setup_runs.sh: <eval>/<config>/run-1/repo is a git repo
committed once as "init", and the agent wrote its reply to outputs/final_message.md.
The grader diffs the repo against that commit, copies any new file into
outputs/ so the viewer shows it, and writes <run>/grading.json.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OFFLINE_CACHE = (HERE / "fixtures/handoffs/offline-cache.md").read_text()
EXISTING = (HERE / "fixtures/project-collision-existing.md").read_text()
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


def repo_changes(repo):
    status = git(repo, "status", "--porcelain", "--untracked-files=all").splitlines()
    return {
        "untracked": [l[3:] for l in status if l.startswith("??")],
        "modified": [l[3:] for l in status if not l.startswith("??")],
        "staged": git(repo, "diff", "--cached", "--name-only").split(),
        "commits": len(git(repo, "log", "--oneline").splitlines()),
    }


class Grader:
    def __init__(self, run):
        self.run = run
        self.repo = run / "repo"
        self.ch = repo_changes(self.repo)
        msg = run / "outputs/final_message.md"
        self.msg = msg.read_text() if msg.exists() else ""
        self.results = []

    def check(self, text, passed, evidence):
        self.results.append({"text": text, "passed": bool(passed), "evidence": evidence})

    def nothing_committed(self):
        c = self.ch
        self.check("Nothing staged or committed",
                   not c["staged"] and c["commits"] == 1,
                   f"staged={c['staged']} commits={c['commits']}")

    def nothing_written(self):
        c = self.ch
        self.check("No file written or modified in the repo",
                   not c["untracked"] and not c["modified"],
                   f"untracked={c['untracked']} modified={c['modified']}")

    def msg_has(self, text, *patterns):
        hits = [p for p in patterns if re.search(p, self.msg, re.I | re.S)]
        self.check(text, len(hits) == len(patterns),
                   f"matched {hits} of {list(patterns)}; message: {self.msg[:300]!r}")


def grade_happy(g):
    new = g.ch["untracked"]
    self_file = new[0] if len(new) == 1 else None
    g.check("Exactly one new file, in docs/decisions/",
            self_file and self_file.startswith("docs/decisions/") and self_file.count("/") == 2,
            f"untracked={new}")
    name = Path(self_file).name if self_file else ""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$", name)
    g.check("Filename date is 2026-09-20 (from the Date line)",
            m and m.group(1) == "2026-09-20", f"filename={name!r}")
    slug = m.group(2) if m else ""
    g.check("Slug is ASCII lowercase kebab-case, at most 5 words and 50 chars",
            SLUG_RE.match(slug) and len(slug.split("-")) <= 5 and len(slug) <= 50,
            f"slug={slug!r} ({len(slug.split('-'))} words, {len(slug)} chars)")
    g.check("Slug transliterates façade and drops the generic word 'decision'",
            "facade" in slug.split("-") and "decision" not in slug.split("-"),
            f"slug={slug!r}")
    body = (g.repo / self_file).read_text() if self_file else ""
    g.check("Outer ```markdown fence stripped, inner ```ts fence kept",
            not body.startswith("```") and "```ts" in body,
            f"first line={body.splitlines()[0] if body else None!r}")
    g.check("Content identical to the pasted handoff (up to trailing newline)",
            body.rstrip("\n") == OFFLINE_CACHE.rstrip("\n") and body.endswith("\n"),
            "identical" if body.rstrip("\n") == OFFLINE_CACHE.rstrip("\n") else
            "differs: " + "".join(__import__("difflib").unified_diff(
                OFFLINE_CACHE.splitlines(True), body.splitlines(True), n=0))[:400])
    g.check("No other project file created or modified (implementation not started)",
            len(new) <= 1 and not g.ch["modified"],
            f"untracked={new} modified={g.ch['modified']}")
    g.nothing_committed()
    g.msg_has("Final message gives the saved path and asks whether to start implementing",
              r"docs/decisions/2026-09-20", r"implement\w*[^\n]*\?")


def grade_missing_dir(g):
    g.check("docs/decisions/ was not created", not (g.repo / "docs").exists(),
            f"docs exists={(g.repo / 'docs').exists()}")
    g.nothing_written()
    g.nothing_committed()
    g.msg_has("Asks whether to create docs/decisions/ or use another path",
              r"docs/decisions", r"creat", r"\?")


def grade_collision(g):
    existing = g.repo / "docs/decisions/2026-09-24-rate-limiting-public-api.md"
    g.check("Existing 2026-09-24-rate-limiting-public-api.md untouched",
            existing.exists() and existing.read_text() == EXISTING,
            "unchanged" if existing.exists() and existing.read_text() == EXISTING else "changed or gone")
    g.nothing_written()
    g.nothing_committed()
    g.msg_has("Uses today's date: message names 2026-09-24-rate-limiting-public-api.md",
              r"2026-09-24-rate-limiting-public-api")
    g.msg_has("Offers overwrite vs suffix", r"overwrite", r"-2|suffix")


def grade_no_content(g):
    g.nothing_written()
    g.nothing_committed()
    g.msg_has("Asks the user to paste the handoff", r"paste")


GRADERS = {
    "happy-path-fenced-accented-title": grade_happy,
    "default-dir-missing": grade_missing_dir,
    "collision-with-placeholder-date": grade_collision,
    "no-content-pasted": grade_no_content,
}


def main(iteration):
    for eval_dir in sorted(Path(iteration).glob("eval-*")):
        name = json.loads((eval_dir / "eval_metadata.json").read_text())["eval_name"]
        for run in sorted(eval_dir.glob("*/run-*")):
            g = Grader(run)
            for f in g.ch["untracked"]:  # surface whatever the run wrote in the viewer
                shutil.copy(g.repo / f, g.run / "outputs" / Path(f).name)
            GRADERS[name](g)
            passed = sum(r["passed"] for r in g.results)
            total = len(g.results)
            (run / "grading.json").write_text(json.dumps({
                "expectations": g.results,
                "summary": {"passed": passed, "failed": total - passed, "total": total,
                            "pass_rate": round(passed / total, 2)},
            }, indent=2))
            print(f"{eval_dir.name}/{run.parent.name}: {passed}/{total}")
            for r in g.results:
                if not r["passed"]:
                    print(f"   FAIL {r['text']} -- {r['evidence'][:200]}")


if __name__ == "__main__":
    main(sys.argv[1])
