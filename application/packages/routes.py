from flask import render_template


# route
def index():
  return render_template('lobby.html')

def index_admin(id, token):
  return render_template('lobby.html')


def login():
  return render_template('login.html')


def get_purchase_room(id, room_token):
  return render_template('room_mobile.html')


def get_purchase_room_admin(id, room_token, user_id, token, state):
  return render_template('room_mobile.html')



def get_inventory_room(id, room_token):
  return render_template('room_inventory_mobile.html')


def get_inventory_room_admin(id, room_token, user_id, token, state):
  return render_template('room_inventory_mobile.html')