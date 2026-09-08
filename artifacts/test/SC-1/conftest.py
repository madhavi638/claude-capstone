from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from config.settings import Settings, load_settings
from utils.testdata import TestData


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def testdata() -> TestData:
    return TestData()


@pytest.fixture(scope="session")
def browser(settings: Settings) -> Browser:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=settings.headless)
    yield browser
    browser.close()
    playwright.stop()


@pytest.fixture(scope="function")
def context(browser: Browser, settings: Settings) -> BrowserContext:
    context = browser.new_context(viewport=settings.viewport)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session", autouse=True)
def ensure_output_dirs(settings: Settings) -> None:
    for folder in (settings.report_dir, settings.screenshot_dir, settings.log_dir):
        folder.mkdir(parents=True, exist_ok=True)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    page = item.funcargs.get("page")
    settings = item.funcargs.get("settings")
    if page is None or settings is None:
        return

    safe_name = item.nodeid.replace("/", "_").replace("::", "_").replace("[", "_").replace("]", "_")
    screenshot_path = settings.screenshot_dir / f"{safe_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
