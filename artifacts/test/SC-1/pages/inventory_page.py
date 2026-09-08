from __future__ import annotations

from locators.inventory_locators import (
    BURGER_MENU_BUTTON,
    INVENTORY_ITEM_DESC,
    INVENTORY_ITEM_IMAGE,
    INVENTORY_ITEM_NAME,
    INVENTORY_ITEM_PRICE,
    INVENTORY_ITEMS,
    LOGOUT_LINK,
    PRODUCTS_TITLE,
    SHOPPING_CART_BADGE,
    SHOPPING_CART_LINK,
)
from pages.base_page import BasePage


class InventoryPage(BasePage):
    def open_inventory_route(self, base_url: str) -> None:
        self.open(f"{base_url.rstrip('/')}/inventory.html")

    def is_loaded(self) -> bool:
        return self.page.locator(PRODUCTS_TITLE).is_visible() and self.page.locator(INVENTORY_ITEMS).count() > 0

    def visible_cards(self):
        cards = self.page.locator(INVENTORY_ITEMS)
        return [cards.nth(index) for index in range(cards.count()) if cards.nth(index).is_visible()]

    def assert_card_details(self) -> None:
        for card in self.visible_cards():
            assert card.locator(INVENTORY_ITEM_NAME).is_visible()
            assert card.locator(INVENTORY_ITEM_DESC).is_visible()
            assert card.locator(INVENTORY_ITEM_PRICE).is_visible()
            assert card.locator(INVENTORY_ITEM_IMAGE).is_visible()

    def add_product(self, product_name: str) -> None:
        card = self.page.locator(INVENTORY_ITEMS).filter(has=self.page.get_by_text(product_name, exact=True)).first
        card.locator("button").click()

    def remove_product(self, product_name: str) -> None:
        card = self.page.locator(INVENTORY_ITEMS).filter(has=self.page.get_by_text(product_name, exact=True)).first
        card.locator("button").click()

    def cart_badge_count(self) -> int:
        badge = self.page.locator(SHOPPING_CART_BADGE)
        if not badge.is_visible():
            return 0
        return int(badge.inner_text())

    def open_cart(self) -> None:
        self.page.locator(SHOPPING_CART_LINK).click()

    def open_menu(self) -> None:
        self.page.locator(BURGER_MENU_BUTTON).click()

    def logout(self) -> None:
        self.open_menu()
        self.page.locator(LOGOUT_LINK).click()
