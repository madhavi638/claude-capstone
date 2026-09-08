# SC-1 Python UI Automation Framework

Generated Playwright + pytest automation assets for the SauceDemo SC-1 feature file.

## Contents

- `tests/` scenario tests generated from `ui_scenarios_SC-1.feature`
- `pages/` page objects for login, inventory, cart, and checkout flows
- `locators/` reusable selectors
- `utils/` test data and browser helpers
- `config/` runtime settings
- `testdata/` dynamic test data inputs
- `conftest.py` shared pytest fixtures and failure screenshots
- `run_tests.py` convenience runner that writes reports into this folder

## Run

```bash
pip install -r artifacts/test/SC-1/requirements.txt
python -m playwright install
python artifacts/test/SC-1/run_tests.py
```

Reports are written to `artifacts/test/SC-1/reports/`.
