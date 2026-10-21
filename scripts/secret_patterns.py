"""Shapes of credentials that must never be committed. Shared by the commit hook and the tests."""

import re

PATTERNS = {
    "OpenAI key": re.compile(r"sk-(?:proj-|admin-)?[A-Za-z0-9_-]{32,}"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}"),
    "AWS key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Azure storage key": re.compile(r"AccountKey=[A-Za-z0-9+/]{40,}={0,2}"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "Service-account JSON": re.compile(r'"private_key_id"\s*:'),
}
