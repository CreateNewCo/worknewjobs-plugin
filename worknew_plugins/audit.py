"""Check publishable files for known secret patterns and private route shapes."""

import re
import subprocess

from .contract import ROOT, ContractError

PATTERNS = (
    r"/api_[a-z0-9]{8,}(?:/|\b)",
    r"/[a-z]+_[a-z0-9_]{16,}(?:/|\b)",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{20,}",
    r"\bAKIA[A-Z0-9]{16}\b",
    r"(?i)\b(?:api_?key|token|password|client_?secret)[\"']?\s*[:=]\s*[\"'][^\s\"']{12,}[\"']",
)


def audit_bytes(contents):
    """Reject recognizable private data without printing the matched value."""
    text = contents.decode("utf-8", errors="replace")
    if any(re.search(pattern, text) for pattern in PATTERNS):
        raise ContractError("Publication audit detected a secret pattern or private endpoint reference")


def audit_repository(root=ROOT):
    """Scan tracked and untracked publishable files, honoring gitignore for local data."""
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=root, check=True, capture_output=True)
    names = set(result.stdout.decode().split("\0")) - {""}
    for name in names:
        path = root / name
        if not path.exists():
            continue
        if path.is_symlink():
            raise ContractError("Publication audit refuses symlinked source files")
        if path.name.startswith(".env") or path.suffix in {".pem", ".key", ".p12", ".pfx"}:
            raise ContractError("Publication audit detected a credential file")
        try:
            audit_bytes(path.read_bytes())
        except ContractError:
            raise ContractError(f"Publication audit failed in {name}; matched content was suppressed") from None
    return len(names)
