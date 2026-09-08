# Test Script Generator Agent — Operation Instructions

---

## 1. Input Requirements

- **Accept BDD Gherkin feature files** (e.g., `ui_scenarios_SC-1.feature`) as input.
- **Extract the ticket ID** (e.g., `SC-1`) from the feature file name.

---

## 2. Parse Feature Files

- **Read and interpret** Given-When-Then scenarios.
- **Identify** all steps, hooks, and data requirements.

---

## 3. Generate Python Test Automation Scripts

For each scenario:

- **Create step definition files**  
  (e.g., `test_ui_steps.py` for `pytest-bdd` or `behave`).
- **Implement steps** to interact with UI elements  
  (e.g., using Selenium, Playwright).
- **Generate setup/teardown hooks**  
  (e.g., `conftest.py` for pytest or `environment.py` for behave).
- **Create test runner scripts** if needed  
  (e.g., `run_tests.py` or use pytest/behave CLI).
- **Generate data model classes** if needed.
- **Ensure all code follows Python best practices** and project conventions.

---

## 4. Validate Code Quality

- **Ensure scripts are syntactically correct** and pass linting  
  (e.g., `flake8`, `pylint`).
- **Check for dynamic test data usage** (no hard-coded values).
- **Validate proper UI element handling and selectors**.

---

## 5. Output Storage

- **Save all generated test scripts** in  
  `artifacts/test/<ticket_id>/`  
  (e.g., `artifacts/test/SC-1/`).
- **Use clear and consistent file naming** within the ticket-specific folder.

---

## 6. Formatting & Alignment

- **Maintain consistent Python code formatting and indentation** (PEP 8).
- **Use VSCode tools and Python linters** to check code quality and alignment.

---

## 7. Objective

Generate a complete executable automation framework, not just test scripts.

## 8. Framework Structure

project_root/
├── tests/
├── pages/
├── locators/
├── utils/
├── config/
├── testdata/
├── reports/
├── screenshots/
├── logs/
├── conftest.py
├── pytest.ini
├── requirements.txt
└── README.md
Generation Rules
Read BDD feature files.
Generate Page Object Model classes.
Generate locator files.
Generate reusable utility modules.
Generate pytest fixtures in conftest.py.
Generate configuration management.
Generate test data files.
Generate pytest test files.
---

## Best Practices

- Use clear, maintainable Python code structure.
- Validate all generated scripts for syntax and compliance.
- Store all test scripts in the designated `artifacts/test/<ticket_id>/` folder for traceability.
- Document any dependencies or required Python packages in the output (e.g., `requirements.txt`).
- Always include the ticket ID in the output path for easy mapping.