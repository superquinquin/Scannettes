from packages.user import User
from packages.room import Room
from packages.odoo import data


class Lobby:
  def __init__(self):
    global data

    data['lobby'] = {'rooms': {},
                     'users': {'admin': {}}}

  # Lobby Rooms
  def create_room(self, input):
    global data

    id = input['id']
    name = input['name']
    password = input['password']
    purchase_id = input['pur']
    rayon_id = input['ray']
    data['lobby']['rooms'][id] = Room(id, name, password, purchase_id, rayon_id)

    return data['lobby']['rooms'][id]
  
  def reset_room(self, id):
    global data

    data['lobby']['rooms'][id].purchase.build_process_tables()

  def delete_room(self, id):
    global data

    data['lobby']['rooms'].pop(id)
  

  # Lobby Users
  def create_user(self, context):
    global data

    ip = context['ip']
    id = context['id']
    loc = context['location']
    admin = context['admin']
    data['lobby']['users'][id] = User(ip, id, loc, admin)


  def move_user(self, id, move):
    global data

    data['lobby']['users'][id].location = move

  def delete_user(self, id):
    global data

    data['lobby']['users'].pop(id)