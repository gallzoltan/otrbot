import logging
from selenium.webdriver.common.by import By
from otrbot.constants import Navigate, TimeoutConfig

class LoginOtr:
  LOGIN_USERNAME_ID = "Login_username"
  LOGIN_PASSWORD_ID = "Login_password"
  LOGIN_BUTTON_ID = "belepes"

  def __init__(self, browser):
    self._browser = browser
    self._logger = logging.getLogger()

  def login(self, url, username, password) -> bool:
    try:
      self._browser.open(url)
      self._signIn(username, password)
      if not self.isLoggedIn(timeout=TimeoutConfig.MEDIUM):
        self._logger.error(f'Login to {url} did not reach the main menu')
        return False
      self._browser.disableAnimations()
      self._logger.info(f'Login to {url} ')
      return True
    except Exception as e:
      self._logger.error(f'Failed to login to {url} due to {str(e)}')
      return False

  def isLoggedIn(self, timeout=TimeoutConfig.SHORT) -> bool:
    return self._browser.isPresent(By.XPATH, Navigate.MENU_TAMOGATASOK.value, timeout=timeout)

  def isLoginPage(self) -> bool:
    return self._browser.isPresent(By.ID, self.LOGIN_USERNAME_ID, timeout=TimeoutConfig.SHORT)

  def _signIn(self, username, password):
    """Sign in to the OTR web client."""
    self._browser.sendKeys(By.ID, self.LOGIN_USERNAME_ID, username)
    self._browser.sendKeys(By.ID, self.LOGIN_PASSWORD_ID, password)
    self._browser.clickElement(By.ID, self.LOGIN_BUTTON_ID)
    self._logger.debug(f'with {username}')

  def _signOut(self):
    """Sign out from the OTR web client."""
    self._browser.close()
