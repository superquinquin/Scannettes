import os
import binascii
from datetime import datetime


class User:
  def __init__(self, id, loc, browser_id, admin ):

    self.id = id
    self.token = self.generate_token()
    self.browser_id = browser_id

    self.last_connection = datetime.now()
    self.is_active = True

    self.admin = admin
    self.location = loc  # [lobby, roomID]

    self.session = 1

  def is_admin(self):
    self.admin = True

  def generate_token(self):
    return binascii.hexlify(os.urandom(20)).decode()  
  
  def verify_permision(self, token):
    if token == self.token:
      return True
    else:
      return False