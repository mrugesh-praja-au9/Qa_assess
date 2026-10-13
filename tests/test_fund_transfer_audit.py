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


def test_setup_creates_two_distinct_accounts(bank_accounts: BankAccounts):
    """Validation 1: Two distinct account numbers are created."""
    assert bank_accounts.account_a != bank_accounts.account_b
    assert bank_accounts.account_a.isdigit()
    assert bank_accounts.account_b.isdigit()


def test_fund_transfer_updates_balances_and_records_transaction_history(bank_accounts: BankAccounts):
    """Validations 2-5: balance accuracy and transaction-history integrity."""
    page = bank_accounts.page
    overview_page = AccountsOverviewPage(page)
    transfer_page = TransferFundsPage(page)
    # The server's own date, not datetime.now(): the ParaBank server's clock
    # may be in a different timezone than whatever runs this suite.
    today = bank_accounts.server_today

    # Step 3: capture balances before transfer.
    overview_page.open()
    balance_a_before = overview_page.get_balance(bank_accounts.account_a)
    balance_b_before = overview_page.get_balance(bank_accounts.account_b)
    logger.info("Before transfer: A=%.2f B=%.2f", balance_a_before, balance_b_before)

    # Step 4: transfer funds from A to B.
    transfer_page.open()
    transfer_page.submit_transfer(TRANSFER_AMOUNT, bank_accounts.account_a, bank_accounts.account_b)
    assert transfer_page.is_transfer_successful(), "Expected the in-limit transfer to succeed"

    # Step 5: capture balances after transfer.
    overview_page.open()
    balance_a_after = overview_page.get_balance(bank_accounts.account_a)
    balance_b_after = overview_page.get_balance(bank_accounts.account_b)
    logger.info("After transfer: A=%.2f B=%.2f", balance_a_after, balance_b_after)

    # Validation 2: balance calculations are accurate (delta-based, not
    # hardcoded absolute values, since opening balances vary per run).
    assert balance_a_after == pytest.approx(balance_a_before - TRANSFER_AMOUNT)
    assert balance_b_after == pytest.approx(balance_b_before + TRANSFER_AMOUNT)

    # Steps 8-9 / Validations 3-5: the transfer is recorded exactly once on
    # both sides of the ledger, with the correct amount and date.
    activity_page = AccountActivityPage(page)

    activity_page.open(bank_accounts.account_a)
    sent_matches = activity_page.count_matching_transactions(TRANSFER_SENT_LABEL, TRANSFER_AMOUNT, today)
    assert sent_matches == 1, (
        f"Expected exactly one '{TRANSFER_SENT_LABEL}' of {TRANSFER_AMOUNT} on {today} "
        f"in account {bank_accounts.account_a}, found {sent_matches}"
    )

    activity_page.open(bank_accounts.account_b)
    received_matches = activity_page.count_matching_transactions(TRANSFER_RECEIVED_LABEL, TRANSFER_AMOUNT, today)
    assert received_matches == 1, (
        f"Expected exactly one '{TRANSFER_RECEIVED_LABEL}' of {TRANSFER_AMOUNT} on {today} "
        f"in account {bank_accounts.account_b}, found {received_matches}"
    )


def test_transfer_exceeding_balance_does_not_crash_the_app(bank_accounts: BankAccounts):
    """Validation 6 (resilience half): an over-limit transfer must not hang
    or throw an unhandled error - the app must land on a definite result or
    error screen."""
    page = bank_accounts.page
    overview_page = AccountsOverviewPage(page)
    transfer_page = TransferFundsPage(page)

    overview_page.open()
    current_balance = overview_page.get_balance(bank_accounts.account_a)
    unrealistic_amount = current_balance + NEGATIVE_PATH_OVERDRAFT_BUFFER

    transfer_page.open()
    transfer_page.submit_transfer(unrealistic_amount, bank_accounts.account_a, bank_accounts.account_b)

    outcome = "success" if transfer_page.is_transfer_successful() else "error"
    logger.info("Over-limit transfer of %.2f resolved with: %s", unrealistic_amount, outcome)
    assert transfer_page.is_transfer_successful() or transfer_page.is_transfer_errored()


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

    overview_page.open()
    current_balance = overview_page.get_balance(bank_accounts.account_a)
    unrealistic_amount = current_balance + NEGATIVE_PATH_OVERDRAFT_BUFFER

    transfer_page.open()
    transfer_page.submit_transfer(unrealistic_amount, bank_accounts.account_a, bank_accounts.account_b)

    assert transfer_page.is_transfer_errored(), "Expected the over-limit transfer to be rejected"
