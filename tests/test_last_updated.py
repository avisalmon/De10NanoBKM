"""The "Last updated" mark on the README.

It exists so that anybody using this blueprint can see, without reading a commit history, when
it last learned something and what. A date typed by hand goes stale the first time a lesson is
added and the date is forgotten, so the mark is computed from docs/lessons_log.md by
scripts/sync_skills.py, and these tests fail while it is behind.
"""

import re
from pathlib import Path

from scripts import sync_skills

ROOT = Path(__file__).resolve().parent.parent


def test_the_newest_lessons_date_is_read_from_the_log():
    when, count = sync_skills.latest_lessons()
    assert re.fullmatch(r"\d{1,2} [A-Z][a-z]+ \d{4}", when), when
    assert count >= 1


def test_the_readme_shows_the_newest_date_and_links_to_the_log():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    when, _count = sync_skills.latest_lessons()
    block = re.search(r"<!-- last-updated:start -->(.*?)<!-- last-updated:end -->", text, re.S)
    assert block, "README.md lost its last-updated markers"
    assert f"Last updated {when}" in block[1]
    assert "lessons_log.md" in block[1]


def test_a_new_lesson_date_makes_the_check_fail_until_the_mark_is_restamped(tmp_path, monkeypatch):
    log = tmp_path / "lessons_log.md"
    log.write_text(
        "# What we learned\n\n## 2099-01-02\n\n- **Something new.** x\n", encoding="utf-8"
    )
    monkeypatch.setattr(sync_skills, "LESSONS", log)
    assert sync_skills.latest_lessons() == ("2 January 2099", 1)
    assert any("README.md" in problem for problem in sync_skills.drift())


def test_the_date_is_written_out_in_full():
    """Never 20/10: half the readers would read it as the twentieth month."""
    when, _count = sync_skills.latest_lessons()
    assert "/" not in when
