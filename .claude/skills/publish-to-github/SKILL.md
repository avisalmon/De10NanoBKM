---
name: publish-to-github
description: >
  Put the owner's FPGA work on GitHub safely: install and log in to the GitHub CLI, check the account,
  use a privacy-safe commit email, run the pre-push check (no build outputs, bitstreams, env or secrets in
  git), create the owner's own repository (ask private or public) while keeping the blueprint as the
  remote "blueprint" for updates, push, watch CI simulate every design, share a bitstream as a GitHub
  Release, and push later changes. Asks before every irreversible or public step.
  TRIGGER: "create the repo", "my own repo", "push", "push to github", "publish", "share my design",
  "share the bitstream", "release", "gh auth login", "github login", "make it private", "make it public",
  "git push", "put this on github", "CI failed", "commit email", "noreply".
---

# Publish to GitHub

Part of the journey ([build-my-fpga-project](../build-my-fpga-project/SKILL.md), Phase 5). Adapted from the same
owner's FullStackBKM blueprint, whose steps were run for real when it was published; the notes marked
(FullStackBKM) were found there.

## Rules (non-negotiable)

1. **Never print, log, commit or paste a token or password.** Do not run `gh auth token`; do not echo `GH_TOKEN`.
   The owner logs in, in a browser.
2. **Ask first** (unless the owner asked for exactly that in this task) before you: create a repository, make one
   public, publish a Release, delete a repository, branch or history, force-push, or rewrite pushed history.
3. **Public means public, forever**: every file in every commit can be read by anyone, even after it is deleted.
4. **Ask whether the owner's repository is private or public.** Suggest private for anything they would not show a
   stranger: a course assignment, an idea from work, something unfinished. Public is fine for a design they want to
   share.
5. **Run the pre-push check before the first push** and before any push that adds many files.
6. **Push only when the owner says so** (CLAUDE.md rule 2). Finish by saying what was published, with the link.

## 1. The GitHub CLI

Check: `gh --version` and `git --version`. Missing: Windows `winget install --id GitHub.cli -e`, macOS
`brew install gh`, Linux https://github.com/cli/cli/blob/trunk/docs/install_linux.md. A `winget` that seems stuck
may be waiting on a Windows permission prompt the owner cannot see (FullStackBKM): ask them to look for it.

## 2. Log in (the owner does one browser step)

```text
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
```

It prints a one-time code and https://github.com/login/device: the owner opens it, signs in **as the right
account**, enters the code. The `workflow` scope lets a push include `.github/workflows/` (this repo's CI). Then:

```text
gh auth status        # the intended account; scopes include repo and workflow
gh auth setup-git     # git uses gh's login for https pushes
```

Many people have two GitHub accounts (a personal one and a work one): confirm which one before creating anything.

## 3. Commit identity: do not publish a work email

Every commit carries an author email, and a public repository publishes it.

* Look: `git config user.email` and `git log --format="%an <%ae>" | sort -u` (PowerShell: `| Sort-Object -Unique`).
* Use the account's **noreply** address, `<numeric-id>+<username>@users.noreply.github.com`: the id is in
  `gh api user --jq .id`, and the owner can check it at https://github.com/settings/emails.
* Set it for this repository (`git config user.email "<noreply>"`, `git config user.name "<Name>"`), or for every
  repository with `--global` if the owner agrees.
* Commits already made with the wrong address and **not yet pushed** can be rewritten: ask first, and follow the
  FullStackBKM skill's `filter-branch` recipe, including deleting the backup refs it leaves. Already pushed: stop
  and tell the owner.

## 4. The pre-push check

In the repository folder; read every result, and show the owner the summary:

```powershell
git status --short                       # nothing unexpected waiting
(git ls-files).Count                     # how many files will be published
git ls-files env .env                    # must print nothing
git ls-files | Select-String -Pattern '(^|/)(db|incremental_db|output_files|qdb|sim_build)/|\.(sof|pof|jic|rbf|vcd)$'   # must print nothing
git grep -nIE "(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}|sk-(proj-|admin-)?[A-Za-z0-9_-]{32,}|AKIA[0-9A-Z]{16}"   # key shapes: must print nothing
.\env\Scripts\python.exe -m pytest -q    # also scans every text file for the shapes in scripts/secret_patterns.py
```

The commit hook (`scripts/check_staged_secrets.py`, installed with `pre-commit install`) blocks the same things
at every commit; CI's gitleaks scan is the last net.

* **No build outputs or bitstreams in git.** They are rebuilt by every compile, they are large, and they change
  every time. The `.gitignore` covers them; a file that was tracked before needs `git rm -r --cached <path>`.
* A file over 100 MB is rejected by GitHub.
* Private material that was ever pushed was public: stop and tell the owner (history rewrite, rotate any key).

## 5. The owner's own repository

The folder is a clone of the blueprint, so `origin` points at `avisalmon/De10NanoBKM`. Keep it under another name,
so that improvements to the blueprint keep arriving (`scripts/check_updates.py` finds it by its URL), and make the
owner's new repository `origin`:

```text
git remote -v                            # origin = the blueprint
git remote rename origin blueprint
gh repo create <account>/<name> --private --source . --remote origin --push --description "One line"
gh repo view <account>/<name> --json visibility,url
```

`--public` instead of `--private` only when agreed (rule 4). Show the owner the URL.

A copy made with GitHub's "Use this template" button has no shared history with the blueprint, so
`check_updates.py` cannot merge updates into it: clone instead.

## 6. CI

Every push runs [.github/workflows/ci.yml](../../../.github/workflows/ci.yml): a secret scan of the whole history
(gitleaks), the linter, the tests, `fpga.py sim --all` (Icarus Verilog simulates the template and **every
project**), and the skill-copy check. Quartus is too big for CI: compiling and programming happen on the owner's
computer.

```text
gh run list --limit 3
gh run watch <run-id> --exit-status
```

Red: `gh run view <run-id> --log-failed`, read it, fix the cause, push again. A failing testbench in CI is a real
failure, not CI's mood.

## 7. Sharing a bitstream: a GitHub Release

A `.sof` never goes into git; a Release attaches it to a version of the code. Ask first (rule 2): on a public
repository, anyone can download it. (Not yet run for real in this blueprint: the flags are from
`gh release create --help`. Check the Release page afterwards.)

```text
gh release create my_counter-v1 projects/my_counter/output_files/my_counter.sof --title "my_counter v1" --notes "DE10-Nano only. Built with Quartus <version>, worst slack <+x> ns. Program it at @2: quartus_pgm -m jtag -c <cable> -o p;my_counter.sof@2"
```

Say in the notes what it does, which Quartus built it, and how it was checked (simulated, seen on the board).

## 8. Later changes

* `git status --short`, then `git add <files>` by name (never a blind `git add -A`), then commit with a message
  that says why.
* Before a commit: `pytest -q`, `ruff check .`, `fpga.py sim --all`, `sync_skills.py --check` (CLAUDE.md rule 7).
* `git push` only on the owner's word. At the start of a session `scripts/check_updates.py` fetches both the
  blueprint and the owner's repository and pulls in what is safe; it never pushes.

## Gotchas

* Windows PowerShell 5.1 has no `&&`: use `;` and check `$LASTEXITCODE`. It also strips double quotes inside
  arguments to programs: do not put JSON or spaced `--jq` expressions in `gh` arguments; use `--jq .field` or
  `ConvertFrom-Json` (FullStackBKM).
* `gh` uses `GH_TOKEN` from the environment instead of the saved login when it is set: `gh auth status` shows which.
* Windows checks files out with CRLF by default; this repo's `.gitattributes` keeps them LF, so files compare equal
  on every computer and in CI (FullStackBKM).
* `gitleaks/gitleaks-action` cannot scan a repository's first push (it asks for the parent of the root commit);
  this repo's CI runs the pinned gitleaks binary over the whole history instead (FullStackBKM).
* Dependabot opens pull requests soon after a repository goes public (FullStackBKM): leave them for the owner and
  merge only with green CI.
* A public repository without a `LICENSE` is "all rights reserved". The blueprint is MIT; for their own repository,
  ask the owner whether to keep it.

## Hand-off checklist

- [ ] The right account; `gh auth status` shows the repo and workflow scopes
- [ ] The commit email is the noreply address; no work email in history about to be published
- [ ] The pre-push check is clean: no `env/`, build outputs, bitstreams or secrets tracked
- [ ] Visibility agreed with the owner
- [ ] `origin` is the owner's repository, `blueprint` is the blueprint; pushed, link shown
- [ ] CI green (`gh run watch --exit-status`)
- [ ] A Release only if the owner asked for one
