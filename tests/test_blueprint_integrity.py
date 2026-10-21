"""Guards for the repository itself: what git may and may not carry, and what CI must run.
Each one is cheap, and each one stands for a mistake that is easy to make once and hard to undo
(a 100 MB build folder in the history, a bitstream mangled by line-ending conversion)."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import fpga

ROOT = Path(__file__).resolve().parent.parent


def test_build_outputs_and_personal_files_are_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for rule in ("env/", ".env", "db/", "incremental_db/", "output_files/", "sim_build/", "*.vcd"):
        assert rule in ignore, rule
    for bitstream in ("*.sof", "*.pof", "*.jic", "*.rbf"):
        assert bitstream in ignore, bitstream


def test_bitstreams_are_binary_to_git():
    """Line-ending conversion on a .sof or .rbf corrupts it without a word of warning."""
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for pattern in ("*.sof", "*.rbf", "*.jic", "*.pof"):
        assert re.search(rf"^{re.escape(pattern)}\s+binary\s*$", attributes, re.M), pattern


@pytest.mark.skipif(not (ROOT / ".git").exists() or not shutil.which("git"), reason="no git repo")
def test_no_build_outputs_are_tracked():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True
    ).stdout.splitlines()
    bad = [
        path
        for path in tracked
        if set(path.split("/")[:-1]) & set(fpga.BUILD_OUTPUTS)
        or path.endswith((".sof", ".rbf", ".jic", ".pof", ".vcd", ".vvp", ".qws"))
    ]
    assert not bad, bad


def test_ci_simulates_every_project_and_checks_the_skills():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for step in (
        "iverilog",
        "pytest",
        "python scripts/fpga.py sim --all",
        "python scripts/sync_skills.py --check",
        "gitleaks",
    ):
        assert step in ci, step


def test_every_template_and_project_has_a_testbench():
    projects = fpga.all_projects()
    assert projects, "no template found"
    for project in projects:
        assert project.testbenches(), f"{fpga.rel(project.dir)} has no sim/tb_*.sv"


def test_the_dev_requirements_point_at_a_real_install_guide():
    text = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    guide = re.search(r"docs/procedures/\S+\.md", text)
    assert guide and (ROOT / guide[0]).is_file()
    assert fpga.INSTALL_GUIDE == guide[0]
