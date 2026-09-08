# SC-1 Phase 2 Test Data Artifact

## Ticket and Scope
- Ticket ID: SC-1
- Feature scope: SauceDemo login, inventory/catalog, cart, checkout, desktop usability/performance
- Source inputs:
  - artifacts/test/SC-1-test-cases.md
  - artifacts/jira/SC-1-jira-details.json
- Generation date: 2026-06-19

## Reusable Baseline Data
These datasets are reusable across multiple scenarios and are referenced by scenario-specific datasets.

| Dataset ID | Type | Purpose | Key Data |
|---|---|---|---|
| SC1-DS-COM-001 | Reusable/Valid | Baseline environment | base_url: https://www.saucedemo.com, route_products: /inventory.html, route_cart: /cart.html, route_checkout_step_one: /checkout-step-one.html |
| SC1-DS-COM-002 | Reusable/Valid | Standard authenticated account | username: standard_user, password: secret_sauce, account_state: active |
| SC1-DS-COM-003 | Reusable/Valid | Inventory product pool | product_1: Sauce Labs Backpack, product_2: Sauce Labs Bike Light, product_3: Sauce Labs Bolt T-Shirt |
| SC1-DS-COM-004 | Reusable/Edge | Desktop baseline profile and SLA | viewport: 1366x768, max_load_seconds: 2.0, network_profile: baseline |

## Scenario-Specific Dataset Catalog

### Login Datasets
| Dataset ID | Type | Scenario Use | Data Payload |
|---|---|---|---|
| SC1-DS-LGN-VAL-001 | Valid | Successful login | username: standard_user, password: secret_sauce, expected_route: /inventory.html |
| SC1-DS-LGN-INV-001 | Invalid | Missing username validation | username: "", password: secret_sauce, expected_error: Epic sadface: Username is required |
| SC1-DS-LGN-INV-002 | Invalid | Missing password validation | username: standard_user, password: "", expected_error: Epic sadface: Password is required |
| SC1-DS-LGN-INV-003 | Invalid | Wrong credential negative path | username: locked_out_user, password: wrong_secret, expected_error: Epic sadface: Username and password do not match any user |
| SC1-DS-LGN-EDGE-001 | Edge | Whitespace input normalization | username: "   ", password: "   ", expected_error: required field validation remains on login |
| SC1-DS-LGN-VAL-002 | Valid | Session persistence after refresh | username: standard_user, password: secret_sauce, post_refresh_expected_route: /inventory.html, cart_icon_visible: true |
| SC1-DS-LGN-INV-004 | Invalid | Unauthenticated direct-route access | session_state: unauthenticated, attempted_route: /inventory.html, expected_route: / |

### Cart Datasets
| Dataset ID | Type | Scenario Use | Data Payload |
|---|---|---|---|
| SC1-DS-CART-VAL-001 | Valid | Single item remove flow | initial_cart_items: [Sauce Labs Backpack], remove_item: Sauce Labs Backpack, expected_badge_after_remove: 0 |
| SC1-DS-CART-VAL-002 | Valid | Non-empty cart checkout navigation | initial_cart_items: [Sauce Labs Backpack, Sauce Labs Bike Light], click_action: Checkout, expected_route: /checkout-step-one.html |
| SC1-DS-CART-INV-001 | Invalid | Remove item not present in cart | initial_cart_items: [Sauce Labs Bike Light], remove_item: Sauce Labs Backpack, expected_result: no removal event for absent item |
| SC1-DS-CART-EDGE-001 | Edge | Badge transition boundary | initial_badge: 1, action: remove_last_item, expected_badge: empty |

### Checkout Datasets
| Dataset ID | Type | Scenario Use | Data Payload |
|---|---|---|---|
| SC1-DS-CHK-VAL-001 | Valid | Checkout info complete | first_name: Test, last_name: User, postal_code: 12345, expected_route: /checkout-step-two.html |
| SC1-DS-CHK-INV-001 | Invalid | Missing first name | first_name: "", last_name: User, postal_code: 12345, expected_error: Error: First Name is required |
| SC1-DS-CHK-INV-002 | Invalid | Missing last name | first_name: Test, last_name: "", postal_code: 12345, expected_error: Error: Last Name is required |
| SC1-DS-CHK-INV-003 | Invalid | Missing postal code | first_name: Test, last_name: User, postal_code: "", expected_error: Error: Postal Code is required |
| SC1-DS-CHK-EDGE-001 | Edge | Minimum postal length boundary | first_name: A, last_name: B, postal_code: 123, expected_result: accepted and continue |
| SC1-DS-CHK-EDGE-002 | Edge | Maximum postal length boundary | first_name: Test, last_name: User, postal_code: A1B2C3D4E5, expected_result: accepted if UI allows length <= 10 |
| SC1-DS-CHK-EDGE-003 | Edge | Name special character boundary | first_name: Anne-Marie, last_name: OConnor, postal_code: 90210, expected_result: accepted and continue |
| SC1-DS-CHK-VAL-002 | Valid | Order completion and cart clear | overview_items: [Sauce Labs Backpack], action: Finish, expected_confirmation: Thank you for your order!, expected_badge_after_finish: empty |

### Usability and Performance Datasets
| Dataset ID | Type | Scenario Use | Data Payload |
|---|---|---|---|
| SC1-DS-FLW-VAL-001 | Valid | Desktop core flow: login | flow: login, viewport: 1366x768, screen_load_targets: [login, inventory], max_load_seconds: 2.0 |
| SC1-DS-FLW-VAL-002 | Valid | Desktop core flow: catalog | flow: catalog, viewport: 1366x768, required_card_fields: [name, image, description, price], max_load_seconds: 2.0 |
| SC1-DS-FLW-VAL-003 | Valid | Desktop core flow: checkout | flow: checkout, viewport: 1366x768, required_controls: [Checkout, Continue, Finish], max_load_seconds: 2.0 |
| SC1-DS-FLW-VAL-004 | Valid | Desktop core flow: logout | flow: logout, viewport: 1366x768, expected_post_logout_route: /, max_load_seconds: 2.0 |
| SC1-DS-FLW-EDGE-001 | Edge | Performance threshold boundary | target_pages: [inventory, cart, checkout-step-one], measured_load_seconds: 1.95-2.00, pass_rule: <=2.0 |

## Explicit Test Case to Dataset Mapping

| Test Case ID | Scenario Title | Dataset IDs |
|---|---|---|
| SC1-TC-001 | Valid login navigates to products | SC1-DS-COM-001, SC1-DS-LGN-VAL-001 |
| SC1-TC-002 | Missing username is validated | SC1-DS-COM-001, SC1-DS-LGN-INV-001 |
| SC1-TC-003 | Missing password is validated | SC1-DS-COM-001, SC1-DS-LGN-INV-002 |
| SC1-TC-004 | Authenticated session survives refresh | SC1-DS-COM-001, SC1-DS-LGN-VAL-002 |
| SC1-TC-005 | Catalog details are visible | SC1-DS-COM-002, SC1-DS-COM-003, SC1-DS-FLW-VAL-002, SC1-DS-FLW-EDGE-001 |
| SC1-TC-006 | Unauthenticated access is blocked | SC1-DS-COM-001, SC1-DS-LGN-INV-004 |
| SC1-TC-007 | Cart remove updates list and badge | SC1-DS-COM-002, SC1-DS-CART-VAL-001, SC1-DS-CART-EDGE-001 |
| SC1-TC-008 | Checkout navigation from cart works | SC1-DS-COM-002, SC1-DS-CART-VAL-002 |
| SC1-TC-009 | Checkout info requires mandatory fields | SC1-DS-COM-002, SC1-DS-CHK-VAL-001, SC1-DS-CHK-INV-001, SC1-DS-CHK-INV-002, SC1-DS-CHK-INV-003, SC1-DS-CHK-EDGE-001, SC1-DS-CHK-EDGE-002, SC1-DS-CHK-EDGE-003 |
| SC1-TC-010 | Successful checkout confirms order and clears cart | SC1-DS-COM-002, SC1-DS-CHK-VAL-001, SC1-DS-CHK-VAL-002 |
| SC1-TC-011 | Desktop core flow usability and performance | SC1-DS-COM-004, SC1-DS-FLW-VAL-001, SC1-DS-FLW-VAL-002, SC1-DS-FLW-VAL-003, SC1-DS-FLW-VAL-004, SC1-DS-FLW-EDGE-001 |

## Data Dictionary

| Field | Type | Constraints | Example | Used In |
|---|---|---|---|---|
| username | string | 1-40 chars for valid input; empty/whitespace for negative tests | standard_user | login, protected route checks |
| password | string | 1-40 chars for valid input; empty for negative tests | secret_sauce | login |
| first_name | string | required for valid checkout; test empty and special-char boundary | Test | checkout info |
| last_name | string | required for valid checkout; test empty and boundary chars | User | checkout info |
| postal_code | string | required; test empty, min length, max length alphanumeric | 12345 | checkout info |
| product_name | string | must match inventory card text exactly | Sauce Labs Backpack | cart and checkout |
| route | string | valid protected/public path in SauceDemo | /inventory.html | auth and navigation |
| viewport | string | desktop baseline for SC-1 core usability | 1366x768 | TC-011 |
| max_load_seconds | number | SLA threshold <= 2.0 seconds | 2.0 | TC-005, TC-011 |
| expected_error | string | deterministic UI error text when invalid action executed | Error: First Name is required | login, checkout |

## Masking and Safety Notes
- All credentials in this artifact are synthetic demo values used in a public training application (SauceDemo), not production credentials.
- No real personal data is used. Names and postal codes are fabricated test strings.
- Do not introduce API tokens, Jira keys, email addresses, or environment secrets into test data files.
- If logs or reports capture test inputs, retain only synthetic values and avoid copying environment variable contents.
- For future datasets, prefer placeholders for sensitive-like fields even in non-production contexts.

## Validation Notes
- Dataset IDs are unique and stable for script-level reuse.
- Data supports positive, negative, and boundary coverage across login, cart, and checkout flows.
- Checkout datasets align with scenario-outline combinations in SC1-TC-009.

## Summary
- Total dataset count: 25
- Reusable baseline datasets: 4
- Scenario-specific datasets: 21
- Mapping completeness: 11 of 11 test cases mapped (100%)
- Coverage by area:
  - Login datasets: 7
  - Cart datasets: 4
  - Checkout datasets: 8
  - Usability/performance datasets: 5
  - Shared baseline datasets: 4
