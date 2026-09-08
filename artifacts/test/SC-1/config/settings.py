from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os


@dataclass(frozen=True)
class Settings:
    base_url: str
    headless: bool
    viewport: dict[str, int]
    report_dir: Path
    screenshot_dir: Path
    log_dir: Path
    testdata_path: Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_settings() -> Settings:
    root = _root()
    return Settings(
        base_url=os.getenv("SAUCEDEMO_BASE_URL", "https://www.saucedemo.com"),
        headless=os.getenv("HEADLESS", "true").strip().lower() not in {"0", "false", "no"},
        viewport={
            "width": int(os.getenv("VIEWPORT_WIDTH", "1280")),
            "height": int(os.getenv("VIEWPORT_HEIGHT", "720")),
        },
        report_dir=root / "reports",
        screenshot_dir=root / "screenshots",
        log_dir=root / "logs",
        testdata_path=root / "testdata" / "sc_1_data.json",
    )


def load_test_data() -> dict[str, str]:
    settings = load_settings()
    if settings.testdata_path.exists():
        return json.loads(settings.testdata_path.read_text(encoding="utf-8"))
    return {}
