import os
import binascii
from datetime import datetime
from application.packages.utils import generate_token


class User:
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

  
  def verify_permision(self, token):
    if token == self.token:
      return True
    else:
      return False