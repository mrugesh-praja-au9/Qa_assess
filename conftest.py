"""Shared fixtures for the ParaBank fund-transfer audit suite."""

from dataclasses import dataclass

import pytest
from playwright.sync_api import Browser, Page

from pages.account_activity_page import AccountActivityPage
from pages.accounts_overview_page import AccountsOverviewPage
from pages.login_page import LoginPage
from pages.open_account_page import AccountType, OpenAccountPage
from pages.registration_page import RegistrationPage
from utils.data_generator import CustomerData, generate_customer
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ProvisionedCustomer:
    """The one customer + two accounts shared by every test in the run."""

    customer: CustomerData
    account_a: str
    account_b: str
    server_today: str


@dataclass(frozen=True)
class BankAccounts:
    """The shared customer's accounts, bound to the current test's page."""

    page: Page
    customer: CustomerData
    account_a: str
    account_b: str
    server_today: str


@pytest.fixture(scope="session")
def provisioned_customer(browser: Browser) -> ProvisionedCustomer:
    """Registers a single customer and opens two accounts once for the whole
    run, instead of re-registering a new customer for every test.

    Runs in its own throwaway context so it doesn't interfere with the
    per-test contexts/pages used afterwards.
    """
    context = browser.new_context()
    page = context.new_page()
    customer = generate_customer()

    logger.info("Registering shared customer username=%s", customer.username)
    registration_page = RegistrationPage(page)
    registration_page.open()
    registration_page.register(customer)
    assert registration_page.is_registration_successful(), "Registration did not confirm success"

    overview_page = AccountsOverviewPage(page)
    overview_page.open()
    default_account_id = overview_page.get_account_ids()[0]
    logger.info("Default account for %s is %s", customer.username, default_account_id)

    open_account_page = OpenAccountPage(page)

    open_account_page.open()
    account_a = open_account_page.open_new_account(AccountType.CHECKING, default_account_id)
    logger.info("Opened checking account A=%s", account_a)

    open_account_page.open()
    account_b = open_account_page.open_new_account(AccountType.SAVINGS, default_account_id)
    logger.info("Opened savings account B=%s", account_b)

    # The ParaBank server's clock/timezone may not match this machine's, so
    # "today" for matching transaction dates must come from the server's own
    # output, not datetime.now(). Account A's $100 opening deposit (just
    # created above) gives us exactly that.
    activity_page = AccountActivityPage(page)
    activity_page.open(account_a)
    server_today = activity_page.get_transactions()[0].date
    logger.info("Server-reported date for today's transactions: %s", server_today)

    context.close()
    return ProvisionedCustomer(
        customer=customer, account_a=account_a, account_b=account_b, server_today=server_today
    )


@pytest.fixture
def bank_accounts(page: Page, provisioned_customer: ProvisionedCustomer) -> BankAccounts:
    """Logs the shared customer into a fresh page for the current test.

    Each test still gets its own browser context/page (so trace, video and
    screenshot capture stay per-test), but reuses the one customer and two
    accounts registered once in `provisioned_customer` instead of
    registering a new user every time.
    """
    customer = provisioned_customer.customer

    login_page = LoginPage(page)
    login_page.open()
    login_page.login(customer.username, customer.password)
    assert login_page.is_login_successful(), "Login did not confirm success"

    return BankAccounts(
        page=page,
        customer=customer,
        account_a=provisioned_customer.account_a,
        account_b=provisioned_customer.account_b,
        server_today=provisioned_customer.server_today,
    )
