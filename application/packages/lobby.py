from typing import Dict
import qrcode
import PIL

from application.packages.user import User
from application.packages.room import Room
from application.packages.utils import is_too_old


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
    
  def update_status(self, id, data, dest):
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


  def generate_qrcode(self, origin, room):
    room_id = room.id
    room_token = room.token
    link = f'{origin}/lobby/{room_id}%26roomtoken%3D{room_token}'
    qrc = qrcode.make(link).convert('RGB')
    
    return qrc
  
  def qrcode_iterator(self, context, data):
    qrcode_list = []
    room_caption = []
    
    origin = context['origin']
    for id in context['room_ids']:
      room = data['lobby']['rooms'][id]
      room_caption.append({'id': room.purchase.name, 
                          'supplier': room.purchase.supplier.name})
      qrcode_list.append(self.generate_qrcode(origin, room))
      
    return {'qrcodes': qrcode_list, 'captions': room_caption}
  
  
  def remove_historic_room(self, odoo, data):
    keys = list(data['lobby']['rooms'].keys())
    for k in keys:
      room = data['lobby']['rooms'][k]
      room_id = room.id
      room_status = room.status
      purchase_id = room.purchase.id
      closing_date = room.closing_date
      if room_status == 'done' and is_too_old(closing_date, 604800):
        self.delete_room(room_id, data)
        odoo.delete_purchase(purchase_id, data)
    
    return data
  
  
  def remove_room_associated_to_purchase(self, data:Dict, purchase_id:int):
    """search room associated to a purchase. if delete = true, fully delete room
      else move it to done.

    Args:
        purchase_id (int): id of the purchase we are looking at.
        purchase_id (Dict): Data dict.
    """
    rooms = list(data['lobby']['rooms'].keys())
    
    for key in rooms:
      room = data['lobby']['rooms'][key]
      room_id = room.id
      room_purchase_id = room.purchase.id
      if room_purchase_id == purchase_id:
        self.delete_room(room_id, data)


  def update_room_associated_to_purchase(self, data:Dict, purchase_id:int, status:str) -> bool:
    updated = False
    rooms = list(data['lobby']['rooms'].keys())
    
    for key in rooms:
      room = data['lobby']['rooms'][key]
      room_purchase_id = room.purchase.id
      if room_purchase_id == purchase_id:
        updated = True
        room.change_status(status)
        
    return updated
      