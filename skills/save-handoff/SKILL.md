---
name: save-handoff
description: Save a pasted brainstorm handoff document (decision record from the brainstorm-handoff skill) into the project as docs/decisions/YYYY-MM-DD-<slug>.md, then offer to start implementing from it.
disable-model-invocation: true
argument-hint: "[target-dir] <pasted handoff markdown>"
---

# Save handoff

The user brainstormed a decision in a chat, got a handoff document out of it, and pasted it here so it lives in the repo as a versioned record. Your job is clerical: put the document in the right place under a predictable name, exactly as written, then hand control back.

## 1. Split the arguments

Everything after `/save-handoff` arrived as:

$ARGUMENTS

- If the first line is a single token with no spaces that doesn't start with `#` (e.g. `docs/adr` or `notes/decisions/`), it is the target directory. Everything after it is the document.
- Otherwise there's no target path and the whole thing is the document.
- If the whole document is wrapped in one outer code fence (```` ```markdown ```` … ```` ``` ````), drop that outer fence — the handoff skill emits its output inside a fence for easy copying, so the fence is packaging, not content. Leave any inner fences alone.

If there is no document — nothing pasted, or only a path — ask the user to paste the handoff markdown and stop there.

## 2. Resolve the target directory

Paths are relative to the repository root (`git rev-parse --show-toplevel`; fall back to the current directory outside a git repo). Default is `docs/decisions/`.

If the directory doesn't exist, don't create it on your own — a new top-level folder is the user's call. Ask whether to create it (the path they gave, or `docs/decisions/` by default) or to use a different path they name, and wait for the answer. If they give a different path, check that one too.

## 3. Build the filename: `YYYY-MM-DD-<slug>.md`

**Date.** Look for a `Date:` line near the top of the document (it usually sits right under the H1, possibly bolded as `**Date:**`). Use it if it's a real calendar date: `2026-09-20` as is, an unambiguous form like `September 20, 2026` converted to `2026-09-20`. If it's missing, a leftover placeholder, invalid (`2026-02-30`), or ambiguous (`09/10/2026`), use today's date.

**Slug.** From the first H1 (`# ...`):

1. Lowercase it and transliterate to ASCII: strip accents (`é` → `e`, `ç` → `c`), expand ligatures (`œ` → `oe`, `ß` → `ss`).
2. Replace every run of non-alphanumeric characters with a single hyphen; trim hyphens at both ends.
3. Drop words every file in the folder would share — `decision`, `adr`, `handoff`, `proposal` — since they don't help tell one record from another.
4. Keep it short: at most 5 words and 50 characters. If it's longer, drop filler words first (articles, prepositions, pronouns, contraction fragments like `ll`), then cut from the end at a word boundary. The slug is for finding the file in a listing, so keep the words that say what was decided.

| H1 | slug |
|---|---|
| `# Use SQLite for the offline cache` | `use-sqlite-offline-cache` |
| `# Decision: naïve retry policy for the sync worker (v2)` | `naive-retry-policy-sync-worker` |
| `# How we'll handle auth token refresh on mobile & web` | `handle-auth-token-refresh-mobile` |

If there's no H1, ask the user for a short name and slugify that.

**Collision.** If the file already exists, don't overwrite it. Ask whether to overwrite it or save alongside with a suffix — the first free of `-2`, `-3`, … before `.md` (`2026-09-20-use-sqlite-offline-cache-2.md`).

## 4. Save verbatim

Write the document exactly as pasted — same headings, wording, whitespace, bullet style, typos. It's a record of what was decided in another conversation, so "improving" it quietly changes the record. The only allowed edits are the outer-fence removal above and making sure the file ends with a single newline.

Don't `git add` or commit; the user decides what goes into history.

## 5. Offer to start

Tell the user the saved path in one line, then ask:

> Start the implementation session from this handoff now?

If they say yes, treat the saved file as the brief: the Decision and Implementation notes are settled — build what they describe rather than reopening the choice. If an Open question blocks the first step, raise it before writing code; the rest can wait until they matter.
