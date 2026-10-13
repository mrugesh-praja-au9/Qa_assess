"""Scenario 6: Multi-Account Fund Transfer Audit (ParaBank).

Each test name maps directly to one line of the assignment's Validation
Criteria table so the mapping is traceable from requirement to assertion:

    1. Two distinct account numbers are created
       -> test_setup_creates_two_distinct_accounts
    2. Balance calculations are accurate
    3. Transaction is recorded in both source and destination accounts
    4. No duplicate transaction is created
    5. Transfer reference appears only once
       -> test_fund_transfer_updates_balances_and_records_transaction_history
    6. System handles invalid transfer gracefully
       -> test_transfer_exceeding_balance_does_not_crash_the_app
       -> test_transfer_exceeding_balance_is_rejected (documents a known
          ParaBank defect; see its docstring and the README)
"""

from datetime import datetime

import allure
import pytest

from config.settings import NEGATIVE_PATH_OVERDRAFT_BUFFER, TRANSFER_AMOUNT
from conftest import BankAccounts
from pages.account_activity_page import AccountActivityPage
from pages.accounts_overview_page import AccountsOverviewPage
from pages.transfer_funds_page import TransferFundsPage
from utils.logger import get_logger

logger = get_logger(__name__)

TRANSFER_SENT_LABEL = "Funds Transfer Sent"
TRANSFER_RECEIVED_LABEL = "Funds Transfer Received"


def _attach_balances(title: str, balance_a: float, balance_b: float) -> None:
    allure.attach(
        f"Account A: ${balance_a:.2f}\nAccount B: ${balance_b:.2f}",
        name=title,
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.epic("ParaBank")
@allure.feature("Scenario 6: Multi-Account Fund Transfer Audit")
@allure.story("Setup")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Opening two new accounts produces two distinct account numbers")
def test_setup_creates_two_distinct_accounts(bank_accounts: BankAccounts):
    """Validation 1: Two distinct account numbers are created."""
    with allure.step("Assert account A and account B are distinct, numeric account IDs"):
        assert bank_accounts.account_a != bank_accounts.account_b
        assert bank_accounts.account_a.isdigit()
        assert bank_accounts.account_b.isdigit()


@allure.epic("ParaBank")
@allure.feature("Scenario 6: Multi-Account Fund Transfer Audit")
@allure.story("Fund transfer & balance audit")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A $250 transfer updates both balances and is recorded exactly once on each side")
def test_fund_transfer_updates_balances_and_records_transaction_history(bank_accounts: BankAccounts):
    """Validations 2-5: balance accuracy and transaction-history integrity."""
    page = bank_accounts.page
    overview_page = AccountsOverviewPage(page)
    transfer_page = TransferFundsPage(page)
    today = datetime.now().strftime("%m-%d-%Y")

    with allure.step("Step 3: capture balances before transfer"):
        overview_page.open()
        balance_a_before = overview_page.get_balance(bank_accounts.account_a)
        balance_b_before = overview_page.get_balance(bank_accounts.account_b)
        logger.info("Before transfer: A=%.2f B=%.2f", balance_a_before, balance_b_before)
        _attach_balances("Balances before transfer", balance_a_before, balance_b_before)

    with allure.step(f"Step 4: transfer ${TRANSFER_AMOUNT:.2f} from account A to account B"):
        transfer_page.open()
        transfer_page.submit_transfer(TRANSFER_AMOUNT, bank_accounts.account_a, bank_accounts.account_b)
        assert transfer_page.is_transfer_successful(), "Expected the in-limit transfer to succeed"

    with allure.step("Step 5: capture balances after transfer"):
        overview_page.open()
        balance_a_after = overview_page.get_balance(bank_accounts.account_a)
        balance_b_after = overview_page.get_balance(bank_accounts.account_b)
        logger.info("After transfer: A=%.2f B=%.2f", balance_a_after, balance_b_after)
        _attach_balances("Balances after transfer", balance_a_after, balance_b_after)

    with allure.step("Validation 2: balance deltas match the transferred amount exactly"):
        # Delta-based, not hardcoded absolute values, since opening balances
        # vary per run.
        assert balance_a_after == pytest.approx(balance_a_before - TRANSFER_AMOUNT)
        assert balance_b_after == pytest.approx(balance_b_before + TRANSFER_AMOUNT)

    activity_page = AccountActivityPage(page)

    with allure.step("Steps 8-9 / Validations 3-4-5: transaction recorded exactly once on account A"):
        activity_page.open(bank_accounts.account_a)
        sent_matches = activity_page.count_matching_transactions(TRANSFER_SENT_LABEL, TRANSFER_AMOUNT, today)
        allure.attach(
            "\n".join(str(t) for t in activity_page.get_transactions()),
            name="Account A activity",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert sent_matches == 1, (
            f"Expected exactly one '{TRANSFER_SENT_LABEL}' of {TRANSFER_AMOUNT} on {today} "
            f"in account {bank_accounts.account_a}, found {sent_matches}"
        )

    with allure.step("Steps 8-9 / Validations 3-4-5: transaction recorded exactly once on account B"):
        activity_page.open(bank_accounts.account_b)
        received_matches = activity_page.count_matching_transactions(TRANSFER_RECEIVED_LABEL, TRANSFER_AMOUNT, today)
        allure.attach(
            "\n".join(str(t) for t in activity_page.get_transactions()),
            name="Account B activity",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert received_matches == 1, (
            f"Expected exactly one '{TRANSFER_RECEIVED_LABEL}' of {TRANSFER_AMOUNT} on {today} "
            f"in account {bank_accounts.account_b}, found {received_matches}"
        )


@allure.epic("ParaBank")
@allure.feature("Scenario 6: Multi-Account Fund Transfer Audit")
@allure.story("Negative-path transfer")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An over-limit transfer always resolves to a definite result, never hangs or crashes")
def test_transfer_exceeding_balance_does_not_crash_the_app(bank_accounts: BankAccounts):
    """Validation 6 (resilience half): an over-limit transfer must not hang
    or throw an unhandled error - the app must land on a definite result or
    error screen."""
    page = bank_accounts.page
    overview_page = AccountsOverviewPage(page)
    transfer_page = TransferFundsPage(page)

    with allure.step("Step 10: read the current balance and attempt a transfer far beyond it"):
        overview_page.open()
        current_balance = overview_page.get_balance(bank_accounts.account_a)
        unrealistic_amount = current_balance + NEGATIVE_PATH_OVERDRAFT_BUFFER
        transfer_page.open()
        transfer_page.submit_transfer(unrealistic_amount, bank_accounts.account_a, bank_accounts.account_b)

    with allure.step("Step 11: verify the app landed on a definite success/error screen"):
        outcome = "success" if transfer_page.is_transfer_successful() else "error"
        logger.info("Over-limit transfer of %.2f resolved with: %s", unrealistic_amount, outcome)
        allure.attach(outcome, name="Over-limit transfer outcome", attachment_type=allure.attachment_type.TEXT)
        assert transfer_page.is_transfer_successful() or transfer_page.is_transfer_errored()


@allure.epic("ParaBank")
@allure.feature("Scenario 6: Multi-Account Fund Transfer Audit")
@allure.story("Negative-path transfer")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An over-limit transfer should be rejected (documents a known app defect)")
@pytest.mark.xfail(
    reason=(
        "Known ParaBank demo-app defect: transfer.htm never validates the "
        "amount against the source account's balance, so it happily sends "
        "the funds and leaves the source account negative instead of "
        "rejecting the request. Documented in README under Known Issues."
    ),
    strict=True,
)
def test_transfer_exceeding_balance_is_rejected(bank_accounts: BankAccounts):
    """Validation 6 (business-rule half): the intended behaviour is that a
    transfer greater than the available balance is rejected."""
    page = bank_accounts.page
    overview_page = AccountsOverviewPage(page)
    transfer_page = TransferFundsPage(page)

    with allure.step("Step 10: read the current balance and attempt a transfer far beyond it"):
        overview_page.open()
        current_balance = overview_page.get_balance(bank_accounts.account_a)
        unrealistic_amount = current_balance + NEGATIVE_PATH_OVERDRAFT_BUFFER
        transfer_page.open()
        transfer_page.submit_transfer(unrealistic_amount, bank_accounts.account_a, bank_accounts.account_b)

    with allure.step("Step 11: verify the transfer was rejected"):
        assert transfer_page.is_transfer_errored(), "Expected the over-limit transfer to be rejected"
