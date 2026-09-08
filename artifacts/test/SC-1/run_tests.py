from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(ROOT),
        "--html",
        str(REPORTS_DIR / "report.html"),
        "--junitxml",
        str(REPORTS_DIR / "junit.xml"),
    ]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
