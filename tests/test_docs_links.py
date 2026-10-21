"""A stranger will click these: every relative markdown link must point at something real."""

import re
from pathlib import Path
from urllib.parse import unquote, urldefrag

ROOT = Path(__file__).resolve().parent.parent
SKIP = {
    "env",
    ".git",
    "node_modules",
    ".ruff_cache",
    ".pytest_cache",
    "db",
    "incremental_db",
    "output_files",
    "sim_build",
}
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"```.*?```", re.S)


def markdown_files():
    return [p for p in ROOT.rglob("*.md") if not SKIP & set(p.relative_to(ROOT).parts)]


def test_every_relative_markdown_link_resolves():
    broken = []
    for path in markdown_files():
        text = FENCE.sub("", path.read_text(encoding="utf-8"))
        for href in LINK.findall(text):
            if re.match(r"^(https?:|mailto:|#)", href) or "<" in href or "{" in href:
                continue
            target = (path.parent / unquote(urldefrag(href)[0])).resolve()
            if not target.exists():
                broken.append(f"{path.relative_to(ROOT)}: {href}")
    assert not broken, "\n".join(broken)


def test_the_link_checker_would_catch_a_broken_link(tmp_path):
    """A test that cannot fail is worse than none."""
    page = tmp_path / "page.md"
    page.write_text("See [the guide](docs/no_such_file.md).", encoding="utf-8")
    (href,) = LINK.findall(page.read_text(encoding="utf-8"))
    assert not (page.parent / href).exists()


def test_the_skills_the_docs_promise_exist():
    skills = {p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md")}
    assert {
        "build-my-fpga-project",
        "setup-my-computer",
        "de10nano-board",
        "simulate-my-design",
        "quartus-build-and-program",
        "fpga-mentor",
        "publish-to-github",
    } <= skills


def test_every_skill_has_frontmatter_with_name_and_triggers():
    for skill in (ROOT / ".claude" / "skills").glob("*/SKILL.md"):
        head = skill.read_text(encoding="utf-8").split("---")[1]
        assert f"name: {skill.parent.name}" in head, skill
        assert "TRIGGER" in head, skill
