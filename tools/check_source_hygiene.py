"""Reject tracked local data and common secret formats without printing values."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]
PATTERNS = {
    "GitHub token": rb"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{40,})",
    "Telegram bot token": rb"\b[0-9]{6,12}:[A-Za-z0-9_-]{30,}\b",
    "private key": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "OpenAI token": rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}",
    "AWS access ID": rb"\bAKIA[A-Z0-9]{16}\b",
}


def main():
    issues = []
    ignored = subprocess.check_output(GIT + ["ls-files", "-ci", "--exclude-standard", "-z"])
    for name in ignored.split(b"\0"):
        if name:
            issues.append(f"Tracked local/generated file: {name.decode('utf-8', 'replace')}")
    paths = subprocess.check_output(GIT + ["ls-files", "-z"]).split(b"\0")
    checked = 0
    for raw in paths:
        if not raw:
            continue
        name = raw.decode("utf-8")
        # Read the index, not the working copy, so staged secrets cannot be
        # hidden by changing the file again before this check runs.
        data = subprocess.check_output(GIT + ["show", f":{name}"])
        checked += 1
        for label, pattern in PATTERNS.items():
            for match in re.finditer(pattern, data):
                line = data[:match.start()].count(b"\n") + 1
                issues.append(f"{name}:{line}: possible {label}; value redacted")
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    print(f"PASS: {checked} tracked files; no ignored artifacts or known secret formats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
