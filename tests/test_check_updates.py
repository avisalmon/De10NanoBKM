"""check_updates.py runs at the start of every session on a newcomer's machine. It must pull what is
safe, refuse what is not, and never leave the folder half-updated. Tested against real git repos."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_updates.py"

pytestmark = pytest.mark.skipif(not shutil.which("git"), reason="needs git")


def git(cwd, *args):
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout


def commit(cwd, name, text, message):
    (cwd / name).write_text(text)
    git(cwd, "add", name)
    git(cwd, "commit", "-q", "-m", message)


@pytest.fixture
def world(tmp_path):
    """An upstream 'blueprint' repo and a user's clone of it, each able to run the real script."""
    upstream = tmp_path / "blueprint"
    upstream.mkdir()
    git(upstream, "init", "-q", "-b", "main")
    git(upstream, "config", "user.email", "b@example.com")
    git(upstream, "config", "user.name", "b")
    commit(upstream, "README.md", "v1\n", "first")
    clone = tmp_path / "mine"
    git(tmp_path, "clone", "-q", str(upstream), str(clone))
    git(clone, "config", "user.email", "u@example.com")
    git(clone, "config", "user.name", "u")
    (clone / "scripts").mkdir()
    shutil.copy(SCRIPT, clone / "scripts" / "check_updates.py")
    git(clone, "add", "scripts")
    git(clone, "commit", "-q", "-m", "add script")

    def run(*extra):
        script = str(clone / "scripts" / "check_updates.py")
        return subprocess.run(
            [sys.executable, script, "--blueprint-url", str(upstream), *extra],
            cwd=clone,
            capture_output=True,
            text=True,
        )

    return upstream, clone, run


def test_up_to_date_says_so(world):
    upstream, clone, run = world
    done = run()
    assert done.returncode == 0 and "up to date" in done.stdout


def test_new_blueprint_updates_are_pulled_and_described(world):
    upstream, clone, run = world
    commit(upstream, "docs.md", "new guide\n", "Better setup guide")
    done = run()
    assert done.returncode == 0, done.stdout
    assert "Better setup guide" in done.stdout and "Pulled in" in done.stdout
    assert (clone / "docs.md").read_text() == "new guide\n"


def test_check_mode_reports_but_changes_nothing(world):
    upstream, clone, run = world
    commit(upstream, "docs.md", "new\n", "Something new")
    done = run("--check")
    assert "Something new" in done.stdout and "nothing changed" in done.stdout
    assert not (clone / "docs.md").exists()


def test_unsaved_changes_block_the_pull(world):
    upstream, clone, run = world
    commit(upstream, "README.md", "v2\n", "Upstream change")
    (clone / "README.md").write_text("my unsaved edit\n")
    done = run()
    assert done.returncode == 2 and "unsaved changes" in done.stdout
    assert (clone / "README.md").read_text() == "my unsaved edit\n"


def test_a_clean_merge_with_the_owners_own_commits_is_applied(world):
    upstream, clone, run = world
    commit(clone, "spec.md", "my design\n", "My spec")
    commit(upstream, "docs.md", "fix\n", "Blueprint fix")
    done = run()
    assert done.returncode == 0, done.stdout
    assert (clone / "spec.md").exists() and (clone / "docs.md").exists()


def test_a_conflict_is_undone_and_reported_never_left_half_done(world):
    upstream, clone, run = world
    commit(clone, "README.md", "the owner's version\n", "Mine")
    commit(upstream, "README.md", "the blueprint's version\n", "Theirs")
    done = run()
    assert done.returncode == 2
    assert "clashes" in done.stdout and "README.md" in done.stdout
    assert (clone / "README.md").read_text() == "the owner's version\n"
    status = git(clone, "status", "--porcelain")
    assert status.strip() == "", "the folder must be left exactly as it was"
    assert not (clone / ".git" / "MERGE_HEAD").exists()


def test_after_the_private_repo_exists_both_sources_are_checked(world, tmp_path):
    upstream, clone, run = world
    own = tmp_path / "own.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(own))
    git(clone, "remote", "rename", "origin", "blueprint")
    git(clone, "remote", "add", "origin", str(own))
    git(clone, "push", "-q", "origin", "main")
    commit(upstream, "docs.md", "new\n", "Blueprint news")
    done = run()
    assert "Blueprint news" in done.stdout and "Your repository: up to date." in done.stdout


def test_no_network_is_reported_and_does_not_crash(world):
    upstream, clone, run = world
    # the remote becomes unreachable, like being offline
    # (deleting the folder fails on Windows: git objects are read-only)
    git(clone, "remote", "set-url", "origin", str(upstream.parent / "no-such-remote"))
    done = subprocess.run(
        [sys.executable, str(clone / "scripts" / "check_updates.py"), "--blueprint-url",
         str(upstream.parent / "no-such-remote")],
        cwd=clone, capture_output=True, text=True,
    )  # fmt: skip
    assert done.returncode == 2 and "could not reach GitHub" in done.stdout


def test_it_never_pushes():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"push"' not in source and "'push'" not in source


def test_every_session_starts_with_the_update_check():
    """The rule is only real if the instructions every assistant reads at the start say so."""
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "0. **Start every session by checking GitHub for updates" in claude
    assert "scripts/check_updates.py" in claude
    skill = (ROOT / ".claude" / "skills" / "build-my-fpga-project" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    orient = skill[skill.index("orient first") : skill.index("1. Read [docs/journey_checklist.md]")]
    assert "check_updates.py" in orient and "re-read" in orient
    copilot = (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert "check_updates.py" in copilot, "Copilot users must get the same rule"
