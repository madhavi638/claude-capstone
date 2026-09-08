from __future__ import annotations

from locators.login_locators import ERROR_CONTAINER, LOGIN_BUTTON, PASSWORD_INPUT, USERNAME_INPUT
from pages.base_page import BasePage


class LoginPage(BasePage):
    def open_login_page(self, base_url: str) -> None:
        self.open(base_url)

    def login(self, username: str, password: str) -> None:
        self.page.locator(USERNAME_INPUT).fill(username)
        self.page.locator(PASSWORD_INPUT).fill(password)
        self.page.locator(LOGIN_BUTTON).click()

    def is_login_form_visible(self) -> bool:
        return self.page.locator(USERNAME_INPUT).is_visible() and self.page.locator(PASSWORD_INPUT).is_visible()

    def error_message(self) -> str:
        return self.page.locator(ERROR_CONTAINER).inner_text()
