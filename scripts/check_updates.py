#!/usr/bin/env python
"""Check GitHub for updates and pull them in when it is safe. Run at the start of every session.

    python scripts/check_updates.py           # fetch, and pull in what is safe
    python scripts/check_updates.py --check   # fetch and report only, change nothing

Two sources of updates:
  * the BLUEPRINT (improvements to the playbooks, docs, template and scripts everyone started
    from). Right after cloning it is the remote `origin`; once the owner has their own
    repository it is the remote `blueprint`.
  * the owner's OWN repository (`origin` once it exists), in case they worked on another computer.

Safety rules (the AI follows the same ones by hand if Python is not installed yet):
  * Unsaved changes in the folder -> pull nothing; say so (commit first, then run again).
  * Only fast-forwards or clean merges are applied. A conflict is undone immediately
    (`git merge --abort`), so the folder is never left half-updated; the files involved are listed.
  * No network -> report and carry on; never block the session.
  * Never pushes. Pushing publishes the owner's work, and that is always the owner's decision.

Exit code 0 = up to date or updated; 2 = something needs attention (the message says what).
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT_URL = "https://github.com/avisalmon/De10NanoBKM"


def git(*args, check=False):
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and done.returncode != 0:
        raise RuntimeError(done.stderr.strip() or done.stdout.strip())
    return done


def normalise(url: str) -> str:
    url = url.strip().rstrip("/")
    return url[:-4] if url.endswith(".git") else url


def remotes() -> dict[str, str]:
    out = {}
    for line in git("remote", "-v").stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "(fetch)":
            out[parts[0]] = normalise(parts[1])
    return out


def is_dirty() -> bool:
    return bool(git("status", "--porcelain", "--untracked-files=no").stdout.strip())


def behind_ahead(ref: str) -> tuple[int, int]:
    counts = git("rev-list", "--left-right", "--count", f"{ref}...HEAD").stdout.split()
    return (int(counts[0]), int(counts[1])) if len(counts) == 2 else (0, 0)


def new_commits(ref: str) -> list[str]:
    return git("log", "--format=%s", f"HEAD..{ref}").stdout.splitlines()


def changed_files(old: str, new: str) -> list[str]:
    return git("diff", "--name-only", old, new).stdout.splitlines()


def advice(files: list[str]) -> list[str]:
    """What the assistant must do after an update, from which files changed."""
    lines = []
    if any(
        f.startswith((".claude/skills/", ".github/skills/", "CLAUDE.md", "AGENTS.md"))
        for f in files
    ):
        lines.append(
            "  Playbooks changed: re-read CLAUDE.md and the skills you are using before continuing."
        )
    if any(f.endswith("requirements-dev.txt") for f in files):
        lines.append(
            "  Dependencies changed: reinstall them (pip install -r requirements-dev.txt in env)."
        )
    if any(f.startswith("templates/") for f in files):
        lines.append(
            "  The project template improved. Your own projects were not touched;"
            " compare them with templates/ if you want the fix."
        )
    lines.append("  Run the tests (pytest -q) before anything else. Nothing was pushed.")
    return lines


def update_from(remote: str, label: str, apply: bool) -> tuple[int, list[str]]:
    """Returns (status, report lines). status 0 = fine, 2 = needs attention."""
    lines = []
    fetch = git("fetch", remote, "--quiet")
    if fetch.returncode != 0:
        return 2, [
            f"{label}: could not reach GitHub ({fetch.stderr.strip()[:120]}). Carrying on offline."
        ]
    branch = "main"
    ref = f"{remote}/{branch}"
    if git("rev-parse", "--verify", "--quiet", ref).returncode != 0:
        return 2, [f"{label}: no branch {branch} on {remote}."]
    if git("merge-base", "HEAD", ref).returncode != 0:
        return 2, [
            f"{label}: this copy has no shared history with {remote} (probably made with"
            " 'Use this template'), so updates can't be merged automatically."
            " Copy individual files by hand, or ask the blueprint's owner."
        ]
    behind, ahead = behind_ahead(ref)
    if behind == 0:
        return 0, [f"{label}: up to date."]
    commits = new_commits(ref)
    lines.append(f"{label}: {behind} new update(s) on GitHub:")
    lines += [f"    - {subject}" for subject in commits[:15]]
    if len(commits) > 15:
        lines.append(f"    ... and {len(commits) - 15} more")
    if not apply:
        return 0, lines + ["  (--check: nothing changed)"]
    if is_dirty():
        return 2, lines + [
            "  Not pulled: there are unsaved changes in this folder."
            " Commit them, then run this again."
        ]
    before = git("rev-parse", "HEAD").stdout.strip()
    if ahead == 0:
        result = git("merge", "--ff-only", ref)
    else:
        result = git("merge", "--no-edit", ref)
    if result.returncode != 0:
        conflicts = git("diff", "--name-only", "--diff-filter=U").stdout.split()
        git("merge", "--abort")
        detail = ", ".join(conflicts) if conflicts else result.stderr.strip()[:160]
        return 2, lines + [
            f"  Not pulled: the update clashes with your own changes in: {detail}.",
            "  Nothing was changed. Resolve it together with the owner"
            " (keep their content, take the update's fixes).",
        ]
    files = changed_files(before, "HEAD")
    lines.append(f"  Pulled in. {len(files)} file(s) changed.")
    return 0, lines + advice(files)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check", action="store_true", help="fetch and report only; change nothing"
    )
    parser.add_argument("--blueprint-url", default=BLUEPRINT_URL, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("Not a git repository: nothing to update.")
        return 2
    known = remotes()
    blueprint = normalise(args.blueprint_url)
    blueprint_remote = next((name for name, url in known.items() if url == blueprint), None)
    own_remote = "origin" if "origin" in known and known["origin"] != blueprint else None

    status, report = 0, []
    if blueprint_remote:
        s, lines = update_from(blueprint_remote, "Blueprint", apply=not args.check)
        status, report = max(status, s), report + lines
    else:
        report.append(
            "Blueprint: no remote points at the blueprint, so there is nothing to check there."
        )
    if own_remote:
        s, lines = update_from(own_remote, "Your repository", apply=not args.check)
        status, report = max(status, s), report + lines
    print("\n".join(report))
    return status


if __name__ == "__main__":
    sys.exit(main())
