from __future__ import annotations

from time import perf_counter

import pytest

from locators.inventory_locators import PRODUCTS_TITLE, SHOPPING_CART_LINK
from locators.login_locators import LOGIN_URL
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from utils.browser_helpers import assert_no_horizontal_overflow


def _login(page, settings, testdata) -> InventoryPage:
    login_page = LoginPage(page)
    login_page.open_login_page(settings.base_url)
    login_page.login(testdata.valid_username, testdata.valid_password)
    inventory_page = InventoryPage(page)
    assert inventory_page.is_loaded()
    return inventory_page


@pytest.mark.auth
@pytest.mark.parametrize(
    ("username", "password", "result_state", "ui_feedback"),
    [
        ("${VALID_USERNAME}", "${VALID_PASSWORD}", "products page is displayed", 'page title "Swag Labs"'),
        ("${EMPTY_USERNAME}", "${VALID_PASSWORD}", "login page remains displayed", "required username error message"),
        ("${VALID_USERNAME}", "${EMPTY_PASSWORD}", "login page remains displayed", "required password error message"),
    ],
)
def test_login_behavior_for_valid_and_required_field_credentials(page, settings, testdata, username, password, result_state, ui_feedback):
    resolved_username = testdata.valid_username if username == "${VALID_USERNAME}" else testdata.empty_username
    resolved_password = testdata.valid_password if password == "${VALID_PASSWORD}" else testdata.empty_password

    login_page = LoginPage(page)
    login_page.open_login_page(settings.base_url)
    login_page.login(resolved_username, resolved_password)

    if result_state == "products page is displayed":
        assert page.locator(PRODUCTS_TITLE).is_visible()
        assert page.title() == "Swag Labs"
    else:
        assert login_page.is_login_form_visible()
        expected_error = "Username is required" if "username" in ui_feedback else "Password is required"
        assert expected_error in login_page.error_message()


@pytest.mark.auth
@pytest.mark.session
def test_authenticated_session_remains_valid_on_refresh(page, settings, testdata):
    inventory_page = _login(page, settings, testdata)
    page.reload()
    assert inventory_page.is_loaded()
    assert page.locator(SHOPPING_CART_LINK).is_visible()


@pytest.mark.catalog
def test_logged_in_shopper_can_view_catalog_details(page, settings, testdata):
    start = perf_counter()
    inventory_page = _login(page, settings, testdata)
    elapsed = perf_counter() - start

    inventory_page.assert_card_details()
    assert elapsed <= 10.0


@pytest.mark.auth_guard
def test_unauthenticated_access_to_products_route_is_blocked(page, settings):
    inventory_page = InventoryPage(page)
    inventory_page.open_inventory_route(settings.base_url)
    assert LoginPage(page).is_login_form_visible()
    assert LOGIN_URL in page.url or page.url.endswith("index.html")


@pytest.mark.cart
def test_remove_item_from_cart_updates_list_and_badge(page, settings, testdata):
    inventory_page = _login(page, settings, testdata)
    inventory_page.add_product(testdata.product_name_1)
    assert inventory_page.cart_badge_count() == 1

    cart_page = CartPage(page)
    cart_page.open_cart_route(settings.base_url)
    assert cart_page.has_product(testdata.product_name_1)

    cart_page.remove_product(testdata.product_name_1)
    assert not cart_page.has_product(testdata.product_name_1)
    assert inventory_page.cart_badge_count() == 0


@pytest.mark.checkout
def test_checkout_navigation_works_from_cart(page, settings, testdata):
    inventory_page = _login(page, settings, testdata)
    inventory_page.add_product(testdata.product_name_1)

    cart_page = CartPage(page)
    cart_page.open_cart_route(settings.base_url)
    cart_page.checkout()

    checkout_page = CheckoutPage(page)
    assert checkout_page.is_information_page()


@pytest.mark.checkout
@pytest.mark.auth_guard
def test_unauthenticated_user_cannot_access_checkout(page, settings):
    checkout_page = CheckoutPage(page)
    checkout_page.open_checkout_information_route(settings.base_url)
    assert LoginPage(page).is_login_form_visible()


@pytest.mark.checkout
@pytest.mark.parametrize(
    ("first_name", "last_name", "postal_code", "result_state", "ui_feedback"),
    [
        ("${CHECKOUT_FIRST}", "${CHECKOUT_LAST}", "${CHECKOUT_POSTAL}", "navigation to checkout overview", "overview page title is displayed"),
        ("${EMPTY_FIRST}", "${CHECKOUT_LAST}", "${CHECKOUT_POSTAL}", "stay on checkout information page", "required first name error"),
        ("${CHECKOUT_FIRST}", "${EMPTY_LAST}", "${CHECKOUT_POSTAL}", "stay on checkout information page", "required last name error"),
        ("${CHECKOUT_FIRST}", "${CHECKOUT_LAST}", "${EMPTY_POSTAL}", "stay on checkout information page", "required postal code error"),
    ],
)
def test_checkout_information_requires_mandatory_fields(page, settings, testdata, first_name, last_name, postal_code, result_state, ui_feedback):
    inventory_page = _login(page, settings, testdata)
    inventory_page.add_product(testdata.product_name_1)

    cart_page = CartPage(page)
    cart_page.open_cart_route(settings.base_url)
    cart_page.checkout()

    checkout_page = CheckoutPage(page)
    resolved_first = testdata.checkout_first if first_name == "${CHECKOUT_FIRST}" else ""
    resolved_last = testdata.checkout_last if last_name == "${CHECKOUT_LAST}" else ""
    resolved_postal = testdata.checkout_postal if postal_code == "${CHECKOUT_POSTAL}" else ""

    checkout_page.fill_information(resolved_first, resolved_last, resolved_postal)
    checkout_page.continue_checkout()

    if result_state == "navigation to checkout overview":
        assert checkout_page.is_overview_page()
        assert "Checkout: Overview" in page.locator(".title").inner_text()
    else:
        expected_error = {
            "required first name error": "First Name is required",
            "required last name error": "Last Name is required",
            "required postal code error": "Postal Code is required",
        }[ui_feedback]
        assert expected_error in checkout_page.error_message()
        assert checkout_page.is_information_page()


@pytest.mark.checkout
def test_shopper_can_complete_purchase_after_valid_checkout_information(page, settings, testdata):
    inventory_page = _login(page, settings, testdata)
    inventory_page.add_product(testdata.product_name_1)

    cart_page = CartPage(page)
    cart_page.open_cart_route(settings.base_url)
    cart_page.checkout()

    checkout_page = CheckoutPage(page)
    checkout_page.fill_information(testdata.checkout_first, testdata.checkout_last, testdata.checkout_postal)
    checkout_page.continue_checkout()
    checkout_page.finish_order()

    assert "Thank you for your order!" in checkout_page.confirmation_message()
    assert inventory_page.cart_badge_count() == 0


@pytest.mark.responsive
@pytest.mark.parametrize(
    ("viewport_profile", "core_flow"),
    [
        ("desktop", "login"),
        ("desktop", "catalog"),
        ("desktop", "checkout"),
        ("desktop", "logout"),
    ],
)
def test_stable_core_shopper_flows_are_usable_on_desktop_viewport(page, settings, testdata, viewport_profile, core_flow):
    if viewport_profile == "desktop":
        page.set_viewport_size({"width": 1280, "height": 720})

    start = perf_counter()
    login_page = LoginPage(page)
    login_page.open_login_page(settings.base_url)

    if core_flow == "login":
        login_page.login(testdata.valid_username, testdata.valid_password)
        assert InventoryPage(page).is_loaded()
        login_page.open_login_page(settings.base_url)
        login_page.login("", "")
        assert "Username is required" in login_page.error_message()
    elif core_flow == "catalog":
        inventory_page = _login(page, settings, testdata)
        inventory_page.assert_card_details()
    elif core_flow == "checkout":
        inventory_page = _login(page, settings, testdata)
        inventory_page.add_product(testdata.product_name_1)
        cart_page = CartPage(page)
        cart_page.open_cart_route(settings.base_url)
        cart_page.checkout()
        checkout_page = CheckoutPage(page)
        checkout_page.continue_checkout()
        assert "First Name is required" in checkout_page.error_message()
    elif core_flow == "logout":
        inventory_page = _login(page, settings, testdata)
        inventory_page.logout()
        assert login_page.is_login_form_visible()

    elapsed = perf_counter() - start
    assert_no_horizontal_overflow(page)
    assert elapsed <= 10.0
