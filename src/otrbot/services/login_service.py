import logging
from selenium.webdriver.common.by import By

class LoginOtr:
  LOGIN_USERNAME_ID = "Login_username"
  LOGIN_PASSWORD_ID = "Login_password"
  LOGIN_BUTTON_ID = "belepes"

  def __init__(self, browser):
    self._browser = browser
    self._logger = logging.getLogger()     

  def login(self, url, username, password):
    try:
      self._browser.driver.get(url=url)
      self._signIn(username, password)
      self._logger.info(f'Login to {url} ')
    except Exception as e:
      self._logger.error(f'Failed to login to {url} due to {str(e)}')

  def _signIn(self, username, password):
    """Sign in to the OTR web client."""
    self._browser.sendKeys(By.ID, self.LOGIN_USERNAME_ID, username)    
    self._browser.sendKeys(By.ID, self.LOGIN_PASSWORD_ID, password)
    self._browser.clickElement(By.ID, self.LOGIN_BUTTON_ID)
    self._logger.debug(f'with {username}')

  def _signOut(self):
    """Sign out from the OTR web client."""
    self._browser.close()
    pass