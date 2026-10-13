"""Page object for the login form on /index.htm."""

from pages.base_page import BasePage


class LoginPage(BasePage):
    URL_PATH = "index.htm"
    USERNAME_INPUT = "form[name='login'] input[name='username']"
    PASSWORD_INPUT = "form[name='login'] input[name='password']"
    LOGIN_BUTTON = "form[name='login'] input[value='Log In']"
    WELCOME_BANNER = "#leftPanel"

    def open(self) -> None:
        self.goto(self.URL_PATH)

    def login(self, username: str, password: str) -> None:
        self.page.fill(self.USERNAME_INPUT, username)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.LOGIN_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def is_login_successful(self) -> bool:
        return "Welcome" in self.page.locator(self.WELCOME_BANNER).inner_text()
