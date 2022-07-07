from application.packages.user import User
from application.packages.room import Room


class Lobby:
  
  def __init__(self):
    pass


  # Lobby Rooms
  def create_room(self, input, data):
    id = input['id']
    name = input['name']
    password = input['password']
    purchase_id = input['pur']
    rayon_id = input['ray']
    data['lobby']['rooms'][id] = Room(id, name, password, purchase_id, rayon_id, data)

    return data['lobby']['rooms'][id]
  
  
  def reset_room(self, id, data):
    data['lobby']['rooms'][id].purchase.build_process_tables()


  def delete_room(self, id, data):
    data['lobby']['rooms'].pop(id)
  

  # Lobby Users
  def create_user(self, context, data):

    ip = context['ip']
    id = context['id']
    loc = context['location']
    admin = context['admin']
    data['lobby']['users'][id] = User(ip, id, loc, admin)


  def move_user(self, id, move, data):
    data['lobby']['users'][id].location = move


  def delete_user(self, id, data):
    data['lobby']['users'].pop(id)
    
    
    
  def get_user_permissions(self, context, data):
    whitelist = open(data['config'].WHITELIST_FILENAME, 'r', encoding='utf-8', errors='ignore')
    
    id  = context['id']
    password = context['password']
    
    for identifier in whitelist.readlines():
      i = identifier.split()
      if id == i[0] and password == i[1]:
        context['permission'] = True
        data['lobby']['users']['admin'][id] = User(id, 'lobby', context['browser'], context['permission'])
        context['token'] = data['lobby']['users']['admin'][id].token
        break
      
    return context 
