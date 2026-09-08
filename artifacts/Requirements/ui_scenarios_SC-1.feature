@SC-1 @ui @saucedemo
Feature: SauceDemo shopper journey for ticket SC-1
  As a shopper
  I want reliable login, catalog, cart, and checkout behavior
  So that I can complete purchases across desktop and mobile devices

  Background:
    Given the application base URL is configured from test environment data
    And the shopper test account credentials are loaded from secure test data

  @US-001 @auth
  Scenario Outline: Login behavior for valid and required-field credentials
    Given I open the "Swag Labs" login page
    When I enter username "<username>" into "Username" input
    And I enter password "<password>" into "Password" input
    And I click the "Login" button
    Then I should observe "<result_state>"
    And I should see "<ui_feedback>"

    Examples:
      | username                | password                | result_state                           | ui_feedback                         |
      | ${VALID_USERNAME}       | ${VALID_PASSWORD}       | products page is displayed             | page title "Swag Labs"             |
      | ${EMPTY_USERNAME}       | ${VALID_PASSWORD}       | login page remains displayed           | required username error message     |
      | ${VALID_USERNAME}       | ${EMPTY_PASSWORD}       | login page remains displayed           | required password error message     |

  @US-001 @session
  Scenario: Authenticated session remains valid on protected page refresh
    Given I log in with valid credentials from test data
    And I am on the products page
    When I refresh the current browser page
    Then I should remain on the products page
    And the cart icon should be visible

  @US-002 @catalog
  Scenario: Logged-in shopper can view catalog details
    Given I log in with valid credentials from test data
    When the products page is fully loaded
    Then each visible product card should display name, image, description, and price
    And the products page should load within 2 seconds under baseline test conditions

  @US-002 @auth-guard
  Scenario: Unauthenticated access to products route is blocked
    Given I am not authenticated
    When I open the products route URL directly
    Then I should be redirected to the login page
    And I should see an authentication-required message or equivalent login prompt

  @US-005 @cart
  Scenario: Remove item from cart updates list and badge
    Given I log in with valid credentials from test data
    And I have products in the cart from test data
    When I open the cart page
    And I remove product "${PRODUCT_NAME_1}"
    Then product "${PRODUCT_NAME_1}" should not be listed in cart
    And cart badge count should update accurately

  @US-006 @checkout
  Scenario: Checkout navigation works from cart
    Given I log in with valid credentials from test data
    And I have at least one product in cart
    When I open the cart page
    And I click the "Checkout" button
    Then I should navigate to the checkout information page

  @US-006 @checkout @auth-guard
  Scenario: Unauthenticated user cannot access checkout
    Given I am not authenticated
    When I open the checkout route URL directly
    Then I should be redirected to the login page

  @US-007 @checkout
  Scenario Outline: Checkout information requires mandatory fields
    Given I log in with valid credentials from test data
    And I have at least one product in cart
    And I am on the checkout information page
    When I enter first name "<first_name>" in "First Name" input
    And I enter last name "<last_name>" in "Last Name" input
    And I enter postal code "<postal_code>" in "Zip/Postal Code" input
    And I click the "Continue" button
    Then I should observe checkout info result "<result_state>"
    And I should see "<ui_feedback>"

    Examples:
      | first_name           | last_name            | postal_code            | result_state                      | ui_feedback                          |
      | ${CHECKOUT_FIRST}    | ${CHECKOUT_LAST}     | ${CHECKOUT_POSTAL}     | navigation to checkout overview   | overview page title is displayed     |
      | ${EMPTY_FIRST}       | ${CHECKOUT_LAST}     | ${CHECKOUT_POSTAL}     | stay on checkout information page | required first name error            |
      | ${CHECKOUT_FIRST}    | ${EMPTY_LAST}        | ${CHECKOUT_POSTAL}     | stay on checkout information page | required last name error             |
      | ${CHECKOUT_FIRST}    | ${CHECKOUT_LAST}     | ${EMPTY_POSTAL}        | stay on checkout information page | required postal code error           |

  @US-008 @checkout
  Scenario: Shopper can complete purchase after valid checkout information
    Given I log in with valid credentials from test data
    And I have completed checkout information with valid data
    When I reach the checkout overview page
    And I click the "Finish" button
    Then I should see the order confirmation message
    And cart badge count should be empty

  @US-010 @responsive
  Scenario Outline: Stable core shopper flows are usable on desktop viewport
    Given I set the viewport to "<viewport_profile>"
    When I execute the core flow "<core_flow>"
    Then pages should render without overlap or broken layout
    And required controls should remain visible and interactable
    And any invalid action should display clear error feedback
    And key screens should load data within 2 seconds under baseline test conditions

    Examples:
      | viewport_profile | core_flow |
      | desktop          | login     |
      | desktop          | catalog   |
      | desktop          | checkout  |
      | desktop          | logout    |
