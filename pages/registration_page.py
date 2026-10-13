"""Page object for /register.htm."""

from pages.base_page import BasePage
from utils.data_generator import CustomerData


class RegistrationPage(BasePage):
    URL_PATH = "register.htm"

    FIRST_NAME = "[id='customer.firstName']"
    LAST_NAME = "[id='customer.lastName']"
    STREET = "[id='customer.address.street']"
    CITY = "[id='customer.address.city']"
    STATE = "[id='customer.address.state']"
    ZIP_CODE = "[id='customer.address.zipCode']"
    PHONE_NUMBER = "[id='customer.phoneNumber']"
    SSN = "[id='customer.ssn']"
    USERNAME = "[id='customer.username']"
    PASSWORD = "[id='customer.password']"
    CONFIRM_PASSWORD = "#repeatedPassword"
    REGISTER_BUTTON = "input[value='Register']"
    CONFIRMATION_BANNER = "#rightPanel h1.title"

    def open(self) -> None:
        self.goto(self.URL_PATH)

    def register(self, customer: CustomerData) -> None:
        self.page.fill(self.FIRST_NAME, customer.first_name)
        self.page.fill(self.LAST_NAME, customer.last_name)
        self.page.fill(self.STREET, customer.street)
        self.page.fill(self.CITY, customer.city)
        self.page.fill(self.STATE, customer.state)
        self.page.fill(self.ZIP_CODE, customer.zip_code)
        self.page.fill(self.PHONE_NUMBER, customer.phone_number)
        self.page.fill(self.SSN, customer.ssn)
        self.page.fill(self.USERNAME, customer.username)
        self.page.fill(self.PASSWORD, customer.password)
        self.page.fill(self.CONFIRM_PASSWORD, customer.password)
        self.page.click(self.REGISTER_BUTTON)
        self.page.wait_for_selector(self.CONFIRMATION_BANNER)

    def is_registration_successful(self) -> bool:
        return "Welcome" in self.page.locator(self.CONFIRMATION_BANNER).inner_text()
