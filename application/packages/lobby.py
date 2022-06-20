from flask import url_for
from flask_socketio import emit

from application import data
from application.packages.user import User
from application.packages.room import Room


class Lobby:
  def __init__(self):
    pass
    # global data

    # data['lobby'] = {'rooms': {},
    #                  'users': {'admin': {}}}

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
    
  def get_user_permissions(self, context):
    id  = context['id']
    password = context['password']
    
    whitelist = open(data['config'].WHITELIST_FILENAME, 'r', encoding='utf-8', errors='ignore')

    for identifier in whitelist.readlines():
      i = identifier.split()
      if id == i[0] and password == i[1]:
        context['permission'] = True
        data['lobby']['users']['admin'][id] = User(id, 'lobby', context['browser'], context['permission'])
        token = data['lobby']['users']['admin'][id].token
        context['url'] = url_for('index_admin', id= id, token= token)
        print(data['lobby'])
        print(data['lobby']['users']['admin'][id].id)
        break
        
    emit('permission', {'permission': context['permission'], 'user_id': id, 'url': context['url']}, include_self=True)