from __future__ import annotations

from config.settings import load_test_data


class TestData:
    def __init__(self) -> None:
        data = load_test_data()
        self.valid_username = data.get("valid_username", "standard_user")
        self.valid_password = data.get("valid_password", "secret_sauce")
        self.empty_username = data.get("empty_username", "")
        self.empty_password = data.get("empty_password", "")
        self.checkout_first = data.get("checkout_first", "Test")
        self.checkout_last = data.get("checkout_last", "User")
        self.checkout_postal = data.get("checkout_postal", "12345")
        self.product_name_1 = data.get("product_name_1", "Sauce Labs Backpack")
        self.product_name_2 = data.get("product_name_2", "Sauce Labs Bike Light")
        self.product_name_3 = data.get("product_name_3", "Sauce Labs Bolt T-Shirt")
