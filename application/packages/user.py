from datetime import datetime
from application.packages.utils import generate_token


class User:
  """ USER INSTANCE
  
  @id (str): is used for cache : cache['lobby']['users'][id]
  @token (str): UNIQUE HEX token that is used to build urls and identify administrators
  @browser_id (str): help to recognize users avoid theft account
  
  @is_active (bool): UNUSED
  @last_connection (str): UNUSED
  @location (str): UNUSED
  @session (int): UNUSED
  
  """
  def __init__(self, id, loc, browser_id, admin ):

    self.id = id
    self.token = generate_token(20)
    self.browser_id = browser_id

    self.last_connection = datetime.now()
    self.is_active = True

    self.admin = admin
    self.location = loc  # [lobby, roomID]

    self.session = 1

  def is_admin(self):
    self.admin = True

  
  def verify_permision(self, token:str):
    if token == self.token:
      return True
    else:
      return False