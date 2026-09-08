from __future__ import annotations

from locators.checkout_locators import (
    CHECKOUT_ERROR,
    CHECKOUT_INFO_TITLE,
    CONFIRMATION_HEADER,
    CONFIRMATION_TEXT,
    CONTINUE_BUTTON,
    FINISH_BUTTON,
    FIRST_NAME_INPUT,
    LAST_NAME_INPUT,
    OVERVIEW_TITLE,
    POSTAL_CODE_INPUT,
)
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    def open_checkout_information_route(self, base_url: str) -> None:
        self.open(f"{base_url.rstrip('/')}/checkout-step-one.html")

    def open_checkout_overview_route(self, base_url: str) -> None:
        self.open(f"{base_url.rstrip('/')}/checkout-step-two.html")

    def is_information_page(self) -> bool:
        return self.page.locator(CHECKOUT_INFO_TITLE).is_visible()

    def is_overview_page(self) -> bool:
        return self.page.locator(OVERVIEW_TITLE).is_visible()

    def fill_information(self, first_name: str, last_name: str, postal_code: str) -> None:
        self.page.locator(FIRST_NAME_INPUT).fill(first_name)
        self.page.locator(LAST_NAME_INPUT).fill(last_name)
        self.page.locator(POSTAL_CODE_INPUT).fill(postal_code)

    def continue_checkout(self) -> None:
        self.page.locator(CONTINUE_BUTTON).click()

    def finish_order(self) -> None:
        self.page.locator(FINISH_BUTTON).click()

    def error_message(self) -> str:
        return self.page.locator(CHECKOUT_ERROR).inner_text()

    def confirmation_message(self) -> str:
        if self.page.locator(CONFIRMATION_HEADER).is_visible():
            return self.page.locator(CONFIRMATION_HEADER).inner_text()
        return self.page.locator(CONFIRMATION_TEXT).inner_text()
