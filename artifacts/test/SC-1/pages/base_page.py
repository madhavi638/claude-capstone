from __future__ import annotations

from playwright.sync_api import Page

from utils.browser_helpers import wait_for_page_ready


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self, url: str) -> None:
        self.page.goto(url)
        wait_for_page_ready(self.page)

    def refresh(self) -> None:
        self.page.reload()
        wait_for_page_ready(self.page)
