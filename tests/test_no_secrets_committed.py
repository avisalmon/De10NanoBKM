"""A cheap last line of defence: no recognisable credential is sitting in a tracked-looking file.

The real defences are .gitignore, the commit hook (scripts/check_staged_secrets.py) and the
gitleaks scan in CI. This catches the case where a key gets pasted into a doc, a test or a script.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {
    "env",
    ".git",
    "node_modules",
    "__pycache__",
    "db",
    "incremental_db",
    "output_files",
    "sim_build",
}
SKIP_FILES = {".env", "test_no_secrets_committed.py"}
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
    ".json",
    ".ps1",
    ".sh",
    ".tcl",
    ".sv",
    ".v",
    ".vh",
    ".svh",
    ".qsf",
    ".qpf",
    ".sdc",
    ".example",
}

spec = importlib.util.spec_from_file_location(
    "secret_patterns", ROOT / "scripts" / "secret_patterns.py"
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)
PATTERNS = _module.PATTERNS


def candidate_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name in SKIP_FILES:
            continue
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        if path.suffix in TEXT_SUFFIXES:
            yield path


def test_no_credentials_in_the_repository():
    hits = []
    for path in candidate_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                hits.append(f"{path.relative_to(ROOT)}: looks like a {label}")
    assert not hits, "\n".join(hits)


def test_the_scanner_would_catch_a_leak():
    """A test that cannot fail is worse than none."""
    fake = "ghp_" + "a" * 36
    assert PATTERNS["GitHub token"].search(f"GH_TOKEN={fake}")
