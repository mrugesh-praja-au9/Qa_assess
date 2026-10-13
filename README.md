# ParaBank Multi-Account Fund Transfer Audit

QA Automation Practical Assessment — Scenario 6 (Dyad Technologies).

Automates: registering a new ParaBank customer, opening two accounts, transferring
funds between them, auditing before/after balances and transaction history, and
exercising the over-limit (negative-path) transfer.

Target site: https://parabank.parasoft.com/parabank/

## Framework

- **Language:** Python 3.11
- **Browser automation:** [Playwright](https://playwright.dev/python/) (sync API)
- **Test runner:** pytest, via the [pytest-playwright](https://github.com/microsoft/playwright-pytest)
  plugin (provides the per-test `page` fixture, and `--tracing` / `--video` /
  `--screenshot` capture on failure)
- **Reporting:** [Allure](https://allurereport.org/) (rich interactive report with
  step timelines, attachments, and failure screenshots) with pytest-html as a
  zero-dependency fallback, plus a file/console logger
- **Design pattern:** Page Object Model — one class per ParaBank page under `pages/`,
  with all locators and interactions encapsulated there; test files only orchestrate
  page objects and assert outcomes.

### Project layout

```
config/           Base URL, timeouts, and scenario constants (transfer amount, etc.)
pages/            Page objects: registration, accounts overview, open account,
                   transfer funds, account activity
utils/            Dynamic test-data generator and the shared logger
conftest.py       bank_accounts fixture: registers a unique customer and opens
                   two accounts (Setup phase, steps 1-2 of the scenario)
tests/            test_fund_transfer_audit.py - the scenario itself
```

## Prerequisites

- Python 3.11+
- Internet access to `parabank.parasoft.com` (this is Parasoft's public demo
  server; no local setup is needed)
- **Optional, only for the Allure report:** a JRE (Java 8+) and the
  [Allure commandline](https://allurereport.org/docs/install/). `pip install`
  alone is enough to *collect* Allure's results (`reports/allure-results/`),
  but turning them into the HTML report needs the Java-based CLI. The suite
  runs and the pytest-html report works fine without either.
  - Windows: `winget install EclipseAdoptium.Temurin.21.JRE` then
    `npm install -g allure-commandline` (or `scoop install allure`)
  - macOS: `brew install allure` (bundles its own JRE dependency via brew)
  - Linux: see the Allure docs link above

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
playwright install chromium
```

## Running the tests

```bash
pytest
```

This runs headless by default and writes:
- `reports/allure-results/` — raw Allure results (needs the Allure CLI to view, see below)
- `reports/report.html` — self-contained pytest-html report (no extra tooling needed)
- `logs/run_<timestamp>.log` — structured run log (also echoed to the console
  via `log_cli`)
- `test-results/` — trace/video/screenshot artifacts, captured only for failing
  tests (see `pytest.ini`)

Useful variations:

```bash
pytest --headed                 # watch the browser
pytest -k test_fund_transfer    # run a single test
pytest --browser firefox        # cross-browser (chromium/firefox/webkit)
```

### Viewing the Allure report

Allure's HTML report fetches its data as JSON at runtime, so it must be served
over HTTP, not opened as a raw `file://` path.

```bash
# One-shot: builds a static report/ and serves + opens it in your browser
allure serve reports/allure-results

# Or generate a static report you can keep/host, then open it
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

The report includes: a pass/fail overview with the target URL/browser/Python
version (from `environment.properties`), tests grouped by Epic → Feature →
Story, a step-by-step timeline per test (register → open accounts → capture
balances → transfer → verify activity) with account numbers and balances
attached inline, and a screenshot automatically attached to any failing test.

## How the scenario maps to the tests

`tests/test_fund_transfer_audit.py` has one test per validation-criteria group,
so the mapping from requirement to assertion is traceable:

| Validation Criteria | Test |
| --- | --- |
| 1. Two distinct account numbers are created | `test_setup_creates_two_distinct_accounts` |
| 2. Balance calculations are accurate | `test_fund_transfer_updates_balances_and_records_transaction_history` |
| 3. Transaction is recorded in both source and destination accounts | same |
| 4. No duplicate transaction is created | same |
| 5. Transfer reference appears only once | same |
| 6. System handles invalid transfer gracefully | `test_transfer_exceeding_balance_does_not_crash_the_app` + `test_transfer_exceeding_balance_is_rejected` |

The Setup phase (steps 1-2: register a new user, open two new accounts) runs
**once per test session**, not once per test — see the session-scoped
`provisioned_customer` fixture in `conftest.py`. Every test then logs that
same customer into its own fresh page via the function-scoped `bank_accounts`
fixture, so tests still get isolated browser contexts (trace/video/screenshot
capture stays per-test) without re-registering a brand-new ParaBank user for
every single test.

Balance assertions are **delta-based** (`balance_after == balance_before -
TRANSFER_AMOUNT`), not hardcoded absolute values. This matters doubly now
that accounts are shared across tests: balances carry over between tests
(e.g. account A is already negative by the time the negative-path tests run),
so any assertion based on an absolute starting balance would be wrong — only
relative deltas are correct regardless of execution order or prior test
activity on the same accounts.

## Assumptions

- **Account funding for the two new accounts.** ParaBank requires a minimum
  $100 deposit from an *existing* account when opening a new one. The fixture
  discovers the customer's original default account dynamically (via the
  Accounts Overview page, not a hardcoded ID) and funds both new accounts
  from it, so opening balances are whatever that flow produces rather than a
  fixed number — balance assertions are written accordingly.
- **"A specific amount (e.g., $250)"** — implemented literally as $250
  (`config/settings.py:TRANSFER_AMOUNT`), configurable in one place.
- **"An unrealistic amount"** for the negative-path step is computed as the
  account's *current* live balance plus a large buffer (`$1,000,000`), read
  dynamically rather than hardcoded, so it is always guaranteed to exceed
  whatever the account's balance actually is at that point in the run.
- **Transaction date matching** uses the server's displayed format
  (`MM-DD-YYYY`, e.g. `10-13-2026`), generated via `datetime.now()` rather
  than hardcoded, to match transactions made "today" during the test run.

## Known issue found during automation (negative-path transfer)

While automating the negative-path step (Workflow steps 10-11), the suite
found that **ParaBank's demo backend does not validate a transfer amount
against the source account's available balance**. Submitting a transfer far
larger than the account's balance returns `Transfer Complete!` and leaves the
source account with a large negative balance, instead of being rejected.

This is a defect in the target demo application, not in the automation. It is
captured as two separate tests rather than papered over:

- `test_transfer_exceeding_balance_does_not_crash_the_app` — asserts the
  resilience half of Validation 6: the app always resolves to a definite
  success/error screen, never hangs or throws an unhandled error. This test
  passes.
- `test_transfer_exceeding_balance_is_rejected` — asserts the *intended*
  business rule (an over-limit transfer should be rejected). It is marked
  `@pytest.mark.xfail(strict=True)` with the defect explained inline, so the
  suite documents the expected behaviour and will loudly fail (XPASS) if
  ParaBank's backend is ever fixed to actually reject it — rather than
  silently asserting the wrong thing is correct.

## Notes on waits

No `time.sleep()` / hardcoded waits anywhere. ParaBank's account balances and
dropdown options are populated by asynchronous AJAX calls after page load, so
page objects wait on the actual DOM condition that matters (a specific account
row appearing, a `<select>`'s options being populated, a result/error panel
becoming visible) rather than a fixed delay. See `pages/account_activity_page.py`
for a case where a naive combined CSS selector picked the wrong element and had
to be replaced with an explicit JS predicate — described in that file and in
the corresponding commit.
