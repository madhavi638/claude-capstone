# Jira Ticket Summary

## Ticket ID
SC-1

## Validation Status
- Ticket existence: unverified (direct Jira API fetch not executed from current toolset)
- Validation method: workspace artifact inference only

## Summary
SauceDemo shopper journey for ticket SC-1

## User Story
As a shopper,
I want reliable login, catalog, cart, and checkout behavior,
So that I can complete purchases across desktop and mobile devices.

## Description
The SC-1 scope covers end-to-end SauceDemo user flow validation across authentication, product browsing, cart management, and checkout completion, with usability/performance expectations.

## Acceptance Criteria
- Valid login redirects to products page.
- Missing username/password shows clear validation or error feedback.
- Protected session remains valid after refresh while authenticated.
- Product catalog shows name, image, description, and price.
- Unauthenticated direct access to protected routes redirects to login.
- Removing cart items updates cart contents and badge count.
- Checkout navigation from cart works when cart has items.
- Checkout information requires first name, last name, and postal code.
- Successful checkout shows confirmation and clears cart state.
- Core desktop flows render without broken layout and show clear errors for invalid actions.
- Key screens load data within 2 seconds under baseline conditions.

## Business Rules
- Only authenticated users can access protected routes and checkout.
- Checkout should be blocked for unauthenticated users and empty-cart state.
- Required checkout fields must be provided before moving to overview/finish.

## Dependencies
- SauceDemo environment availability and reachable base URL.
- Valid test account credentials in secured test data.
- Stable test environment supporting baseline page-load timing.

## Assumptions
- SC-1 represents the consolidated shopper journey ticket used by current STLC artifacts.
- Priority/status/attachments require live Jira fetch and are unknown in local artifacts.

## Source Evidence
- artifacts/Requirements/ui_scenarios_SC-1.feature
- artifacts/Requirements/SRS
- artifacts/test/SC-1/post_quality_gate_update.ps1
- STLC-Capstone/artifacts/git/SC-1/BRANCH_INFO_SC-1.md
