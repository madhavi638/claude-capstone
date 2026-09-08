# SauceDemo User Stories and Acceptance Criteria

Source: Software Requirements Specification

## US-001: Login with valid credentials
As a registered shopper,
I want to log in with a valid username and password,
So that I can access products and purchase items.

Acceptance Criteria:
- Given I am on the login page, when I enter valid credentials and submit, then I am redirected to the Swag Labs page.
- Given I submit invalid credentials, then an error message is displayed and I remain on the login page.
- Given I leave username or password empty, then a clear validation or error message is shown.
- Given I am logged in, when I refresh a protected page, then my authenticated session remains valid until logout or timeout.

## US-002: View product catalog
As a logged-in shopper,
I want to view all available products with details,
So that I can decide what to buy.

Acceptance Criteria:
- Given I am logged in, when products page loads, then each product shows name, image, description, and price.
- Given product data is available, then catalog content is loaded within 2 seconds under normal conditions.
- Given I am not logged in, when I try to access products page directly, then I am redirected to login.
- Given an application or data issue occurs, then a clear error message is shown to the user.

## US-003: Sort products
As a logged-in shopper,
I want to sort products by name and price,
So that I can find items faster.

Acceptance Criteria:
- Given I am on products page, when I choose Name (A to Z), then products are sorted alphabetically ascending.
- Given I choose Name (Z to A), then products are sorted alphabetically descending.
- Given I choose Price (Low to High), then products are sorted by ascending numeric price.
- Given I choose Price (High to Low), then products are sorted by descending numeric price.
- Given sorting is applied, then visible product details remain accurate for each item.

## US-004: Add item to cart
As a logged-in shopper,
I want to add products to my cart,
So that I can purchase selected items later.

Acceptance Criteria:
- Given I am logged in, when I click Add to cart on a product, then that product is added to cart.
- Given an item is added, then cart badge or count updates immediately.
- Given I am not logged in, when I attempt add-to-cart behavior, then access is blocked and I am sent to login.
- Given multiple items are added, then each selected item appears in cart with correct price and quantity.

## US-005: View and manage cart
As a logged-in shopper,
I want to view cart contents and remove items,
So that I can control what I buy.

Acceptance Criteria:
- Given I open the cart, then all selected items are listed with names, quantities, and prices.
- Given an item is in cart, when I remove it, then it no longer appears in cart.
- Given item removal occurs, then cart badge or count updates accurately.
- Given no items remain, then cart displays an empty state and checkout is disabled or blocked.

## US-006: Start checkout
As a logged-in shopper,
I want to proceed to checkout from cart,
So that I can complete my purchase.

Acceptance Criteria:
- Given cart has at least one item, when I click Checkout, then I navigate to checkout information step.
- Given cart is empty, when I click Checkout, then I am blocked with a clear message.
- Given I am not authenticated, when I try to reach checkout, then I am redirected to login.

## US-007: Enter checkout information
As a shopper in checkout,
I want to provide first name, last name, and postal code,
So that my order can be processed.

Acceptance Criteria:
- Given I am on checkout information page, then fields for first name, last name, and postal code are present.
- Given any required field is missing, when I continue, then checkout does not proceed and a clear error message appears.
- Given all required fields are valid, when I continue, then I move to order overview step.
- Given invalid format or empty values are entered, then user-friendly validation feedback is displayed.

## US-008: Review order summary and complete purchase
As a shopper in checkout,
I want to review order summary and finalize purchase,
So that I can place my order confidently.

Acceptance Criteria:
- Given I reach overview step, then I see selected items, pricing, and totals before finishing.
- Given I click Finish with valid checkout state, then order is completed and confirmation or success message is shown.
- Given order completes, then cart is cleared.
- Given checkout prerequisites are not met, then finish action is blocked with clear feedback.

## US-009: Logout securely
As an authenticated user,
I want to log out from any page,
So that my session is securely ended.

Acceptance Criteria:
- Given I am logged in on any page, when I click Logout, then I am redirected to login page.
- Given I have logged out, when I use browser back to protected pages, then access is denied and redirected to login.
- Given logout occurs, then session or auth state is invalidated.

## US-010: Responsive and usable experience
As a shopper,
I want the application to work well on desktop and mobile,
So that I can shop from any device.

Acceptance Criteria:
- Given supported desktop or mobile viewport, then pages render without broken layouts or overlap.
- Given core flows (login, catalog, cart, checkout, logout), then each flow is usable on both desktop and mobile.
- Given invalid user actions, then clear error messages are shown.
- Given product and cart views load, then data appears within 2 seconds under expected environment conditions.
