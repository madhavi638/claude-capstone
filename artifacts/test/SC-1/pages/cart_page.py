from __future__ import annotations

from locators.cart_locators import CART_ITEMS, CART_ITEM_NAME, CART_TITLE, CHECKOUT_BUTTON
from pages.base_page import BasePage


class CartPage(BasePage):
    def open_cart_route(self, base_url: str) -> None:
        self.open(f"{base_url.rstrip('/')}/cart.html")

    def is_loaded(self) -> bool:
        return self.page.locator(CART_TITLE).is_visible()

    def item_names(self) -> list[str]:
        items = self.page.locator(CART_ITEMS)
        return [items.nth(index).locator(CART_ITEM_NAME).inner_text() for index in range(items.count())]

    def has_product(self, product_name: str) -> bool:
        return product_name in self.item_names()

    def remove_product(self, product_name: str) -> None:
        item = self.page.locator(CART_ITEMS).filter(has=self.page.get_by_text(product_name, exact=True)).first
        item.locator("button").click()

    def checkout(self) -> None:
        self.page.locator(CHECKOUT_BUTTON).click()
