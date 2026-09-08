# SC-1 Phase 1 Test Case Artifact

## Ticket
- Ticket ID: SC-1
- Scope: SauceDemo shopper journey (login, catalog, cart, checkout, usability/performance)
- Source Inputs:
  - artifacts/jira/SC-1-user-story.md
  - artifacts/jira/SC-1-jira-details.json
  - artifacts/Requirements/ui_scenarios_SC-1.feature
  - artifacts/Requirements/SRS

## Acceptance Criteria Reference IDs
- AC-01: Valid login redirects to products page.
- AC-02: Missing username/password shows clear validation or error feedback.
- AC-03: Protected session remains valid after refresh while authenticated.
- AC-04: Product catalog shows name, image, description, and price.
- AC-05: Unauthenticated direct access to protected routes redirects to login.
- AC-06: Removing cart items updates cart contents and badge count.
- AC-07: Checkout navigation from cart works when cart has items.
- AC-08: Checkout information requires first name, last name, and postal code.
- AC-09: Successful checkout shows confirmation and clears cart state.
- AC-10: Core desktop flows render without broken layout and show clear errors for invalid actions; key screens load within 2 seconds under baseline conditions.

## Execution Readiness For Test Data Phase
- Test data must be injected dynamically from test data source (no hard-coded credentials or PII).
- Required placeholders:
  - ${VALID_USERNAME}, ${VALID_PASSWORD}
  - ${EMPTY_USERNAME}, ${EMPTY_PASSWORD}
  - ${PRODUCT_NAME_1}
  - ${CHECKOUT_FIRST}, ${CHECKOUT_LAST}, ${CHECKOUT_POSTAL}
  - ${EMPTY_FIRST}, ${EMPTY_LAST}, ${EMPTY_POSTAL}
- Baseline preconditions:
  - SauceDemo base URL is reachable.
  - Test account is active and authorized.
  - Browser and viewport profiles are configured for desktop execution.
  - Timing instrumentation is enabled for page load SLA checks (2-second threshold).

## BDD/Gherkin Scenarios

### SC1-TC-001 - Valid login navigates to products
- Acceptance Criteria: AC-01

```gherkin
Scenario: Valid login redirects shopper to products page
  Given I open the "Swag Labs" login page
  When I enter username "${VALID_USERNAME}" into "Username" input
  And I enter password "${VALID_PASSWORD}" into "Password" input
  And I click the "Login" button
  Then the products page is displayed
  And the page title is "Swag Labs"
```

### SC1-TC-002 - Missing username is validated
- Acceptance Criteria: AC-02

```gherkin
Scenario: Missing username shows validation feedback
  Given I open the "Swag Labs" login page
  When I enter username "${EMPTY_USERNAME}" into "Username" input
  And I enter password "${VALID_PASSWORD}" into "Password" input
  And I click the "Login" button
  Then the login page remains displayed
  And I see a required username error message
```

### SC1-TC-003 - Missing password is validated
- Acceptance Criteria: AC-02

```gherkin
Scenario: Missing password shows validation feedback
  Given I open the "Swag Labs" login page
  When I enter username "${VALID_USERNAME}" into "Username" input
  And I enter password "${EMPTY_PASSWORD}" into "Password" input
  And I click the "Login" button
  Then the login page remains displayed
  And I see a required password error message
```

### SC1-TC-004 - Authenticated session survives refresh
- Acceptance Criteria: AC-03

```gherkin
Scenario: Session remains valid after browser refresh on products page
  Given I am logged in with "${VALID_USERNAME}" and "${VALID_PASSWORD}"
  And I am on the products page
  When I refresh the browser page
  Then I remain on the products page
  And the cart icon remains visible
```

### SC1-TC-005 - Catalog details are visible
- Acceptance Criteria: AC-04, AC-10

```gherkin
Scenario: Product catalog displays complete product card details
  Given I am logged in with "${VALID_USERNAME}" and "${VALID_PASSWORD}"
  When the products page is fully loaded
  Then each visible product card shows name, image, description, and price
  And the products page data loads within 2 seconds under baseline conditions
```

### SC1-TC-006 - Unauthenticated access is blocked
- Acceptance Criteria: AC-05

```gherkin
Scenario: Direct access to products route redirects unauthenticated user to login
  Given I am not authenticated
  When I open the products route URL directly
  Then I am redirected to the login page
  And I see an authentication-required prompt or equivalent login UI
```

### SC1-TC-007 - Cart remove updates list and badge
- Acceptance Criteria: AC-06

```gherkin
Scenario: Removing an item updates cart contents and badge count
  Given I am logged in with "${VALID_USERNAME}" and "${VALID_PASSWORD}"
  And I have product "${PRODUCT_NAME_1}" in my cart
  When I open the cart page
  And I remove product "${PRODUCT_NAME_1}"
  Then product "${PRODUCT_NAME_1}" is no longer listed in the cart
  And cart badge count updates accurately
```

### SC1-TC-008 - Checkout navigation from cart works
- Acceptance Criteria: AC-07

```gherkin
Scenario: Shopper with non-empty cart can navigate to checkout information page
  Given I am logged in with "${VALID_USERNAME}" and "${VALID_PASSWORD}"
  And I have at least one product in cart
  When I open the cart page
  And I click the "Checkout" button
  Then the checkout information page is displayed
```

### SC1-TC-009 - Checkout info requires mandatory fields
- Acceptance Criteria: AC-08

```gherkin
Scenario Outline: Checkout information enforces required fields
  Given I am logged in with "${VALID_USERNAME}" and "${VALID_PASSWORD}"
  And I have at least one product in cart
  And I am on the checkout information page
  When I enter first name "<first_name>" in "First Name" input
  And I enter last name "<last_name>" in "Last Name" input
  And I enter postal code "<postal_code>" in "Zip/Postal Code" input
  And I click the "Continue" button
  Then I should observe checkout result "<result_state>"
  And I should see "<ui_feedback>"

  Examples:
    | first_name        | last_name         | postal_code         | result_state                      | ui_feedback                       |
    | ${CHECKOUT_FIRST} | ${CHECKOUT_LAST}  | ${CHECKOUT_POSTAL}  | navigate to checkout overview     | overview page title is displayed  |
    | ${EMPTY_FIRST}    | ${CHECKOUT_LAST}  | ${CHECKOUT_POSTAL}  | remain on checkout information    | required first name error         |
    | ${CHECKOUT_FIRST} | ${EMPTY_LAST}     | ${CHECKOUT_POSTAL}  | remain on checkout information    | required last name error          |
    | ${CHECKOUT_FIRST} | ${CHECKOUT_LAST}  | ${EMPTY_POSTAL}     | remain on checkout information    | required postal code error        |
```

### SC1-TC-010 - Successful checkout confirms order and clears cart
- Acceptance Criteria: AC-09

```gherkin
Scenario: Shopper completes purchase and cart state is cleared
  Given I am logged in with "${VALID_USERNAME}" and "${VALID_PASSWORD}"
  And I have completed checkout information with valid test data
  And I am on the checkout overview page
  When I click the "Finish" button
  Then I see the order confirmation message
  And cart badge count is empty
```

### SC1-TC-011 - Desktop core flow usability and performance
- Acceptance Criteria: AC-10

```gherkin
Scenario Outline: Desktop core flow remains usable with clear errors and baseline performance
  Given I set viewport profile to "desktop"
  And I am prepared to execute core flow "<core_flow>"
  When I execute the core flow "<core_flow>"
  Then pages render without overlap or broken layout
  And required controls remain visible and interactable
  And invalid actions show clear error feedback
  And key screens in the flow load within 2 seconds under baseline conditions

  Examples:
    | core_flow |
    | login     |
    | catalog   |
    | checkout  |
    | logout    |
```

## Traceability Matrix
| Scenario ID  | Scenario Name                                                | Mapped AC IDs |
|--------------|--------------------------------------------------------------|---------------|
| SC1-TC-001   | Valid login navigates to products                            | AC-01         |
| SC1-TC-002   | Missing username is validated                                | AC-02         |
| SC1-TC-003   | Missing password is validated                                | AC-02         |
| SC1-TC-004   | Authenticated session survives refresh                       | AC-03         |
| SC1-TC-005   | Catalog details are visible                                  | AC-04, AC-10  |
| SC1-TC-006   | Unauthenticated access is blocked                            | AC-05         |
| SC1-TC-007   | Cart remove updates list and badge                           | AC-06         |
| SC1-TC-008   | Checkout navigation from cart works                          | AC-07         |
| SC1-TC-009   | Checkout info requires mandatory fields                      | AC-08         |
| SC1-TC-010   | Successful checkout confirms order and clears cart           | AC-09         |
| SC1-TC-011   | Desktop core flow usability and performance                  | AC-10         |

## Coverage Check
- Total scenarios: 11
- Acceptance criteria covered: 10 of 10
- Traceability completeness: 100%
- Unmapped acceptance criteria: None
