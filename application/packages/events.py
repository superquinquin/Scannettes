from flask import url_for
from flask_socketio import emit, join_room

from application.packages.lobby import Lobby
from application.packages.odoo import Odoo
from .. import socketio, data, odoo, lobby
from .utils import get_passer, get_task_permission
from .pdf import PDF


def task_permission_redirector(data, context) -> bool:
  permission = get_task_permission(data, context['suffix'])
  
  if permission == False:
    emit('task-access-denied', context, include_self=True)

  return permission
  
  

@socketio.on('message')
def handle_my_custom_event(msg):
  print(str(msg))


@socketio.on('ask_permission')
def verify_loggin(context):
  global lobby
  
  context['url'] = ''
  context['permission'] = False
  context = lobby.get_user_permissions(context, data)
  print(context)
  if context['permission'] == True:
    context['url'] = url_for('index_admin', 
                             id= context['id'], 
                             token= context['token'])
  print('ask permision', context)
  emit('permission', 
       context, 
       include_self=True)
  



@socketio.on('verify_connection')
def verify_logger(context):
  global data
  print(context)
  permission = False
  browser_id = context['browser_id']
  suffix = context['suffix']

  passer = get_passer(suffix)
  user_id = passer.get('id',None)
  token = passer.get('token',None)
  state = passer.get('state',None)
  
  roomID = context.get('roomID', None)
  if roomID:
    room = data['lobby']['rooms'][roomID]
    room_state = room.status
  else:
    room_state = 'open'

  if user_id in data['lobby']['users']['admin'].keys():
    user = data['lobby']['users']['admin'][user_id]
    print(user.token, user.browser_id)
    print(token, browser_id)
    if user.token == token and user.browser_id == browser_id:    
      permission = True
      emit('grant_permission', {'permission': permission})
  
  if permission == False and room_state == 'open':
    print('no permissions')
    emit('denied_permission', {'permission': permission}, include_self=True)
  
  elif roomID and permission == False and room_state == 'close':
    print('access denied to closed room')
    emit('no_access_redirection', {'permission': permission,
                                   'url': url_for('index')}, 
                                    include_self=True)
  







@socketio.on('redirect')
def redirect(context):
  global data

  id = context['id']
  password = context['password']
  browser = context['browser_id']
  winWidth = context['winWidth']
  suffix = context['suffix']
  passer = get_passer(suffix)

  room = data['lobby']['rooms'][id]
  room_token = room.token

  if password == room.password:

    if suffix == 'lobby':
      emit('go_to_room', {'url': url_for('get_room', id=id, room_token= room_token)})

    else:
      user_id = passer.get('id',None)

      if user_id in data['lobby']['users']['admin'].keys():
        user = data['lobby']['users']['admin'][user_id]
        token = passer.get('token',None)

        if user.token == token and user.browser_id == browser:
            emit('go_to_room', {'url': url_for('get_room_admin', id= id, room_token= room_token, user_id= user_id, 
                                                                token= token, state= room.status, winWidth=winWidth)})
        
        else:
          emit('go_to_room', {'url': url_for('get_room', id=id, room_token= room_token)})
      
      else:
        emit('go_to_room', {'url': url_for('get_room', id=id, room_token= room_token)})

  else:
    emit('access_denied', context,include_self=True)


@socketio.on('join_lobby')
def join_lobby():
  global data
  print(data)
  print('joining lobby')

  context = {'room': [],
             'selector': []}

  for k in data['lobby']['rooms'].keys():
    id = data['lobby']['rooms'][k].id
    name = data['lobby']['rooms'][k].name
    status = data['lobby']['rooms'][k].status
    date = data['lobby']['rooms'][k].oppening_date
    purchase_name = data['lobby']['rooms'][k].purchase.name
    purchase_supplier = data['lobby']['rooms'][k].purchase.supplier_name
    date_closing = data['lobby']['rooms'][k].closing_date

    context['room'].append([id, name, purchase_name, status, date, purchase_supplier, date_closing])
  
  for k in data['odoo']['purchases']['incoming'].keys():
    id = data['odoo']['purchases']['incoming'][k].id
    name = data['odoo']['purchases']['incoming'][k].name
    purchase_supplier = data['odoo']['purchases']['incoming'][k].supplier_name

    if data['odoo']['purchases']['incoming'][k].real:
      context['selector'].append(tuple((id, name + ' - ' + purchase_supplier)))

    else:
      context['selector'].append(tuple((id, name)))
      
  context['selector'] = sorted(context['selector'],
                              key=lambda x: int(x[0]),
                              reverse=True)
  
  emit('load_existing_lobby', context, include_self=True)


@socketio.on('join_room')
def joining_room(room):
  global data

  room = data['lobby']['rooms'][room]
  name = room.name
  id = room.id
  room_state = room.status
  purchase = room.purchase.name
  purchase_supplier = room.purchase.supplier_name

  html_ent, html_quet, html_dont = room.purchase.table_position_to_html()
  entry_records, queue_records, done_records = room.purchase.get_table_records()


  context = {'room_id': id,
             'room_name': name,
             'purchase_name': purchase,
             'purchase_supplier': purchase_supplier,
            #  'entries_table':html_ent,
            #  'queue_table':html_quet,
            #  'done_table':html_dont,
             'entries_records': entry_records,
             'queue_records': queue_records,
             'done_records': done_records,
             'scanned': room.purchase.scanned_barcodes,
             'new': room.purchase.new_items,
             'mod': room.purchase.modified_items}
  
  emit('load_existing_room', context)


@socketio.on('create_room')
def create_room(input):
  global data
  print('create room')
  room = Lobby().create_room(input, data)

  input['status'] = room.status
  input['users'] = room.users
  input['creation_date'] = room.oppening_date
  input['supplier'] = room.purchase.supplier_name

  if room.purchase.process_status == None:
    room.purchase.build_process_tables()

  emit('add_room', input, broadcast=True, include_self=True)


@socketio.on('del_room')
def del_room(id):
  global data
  
  Lobby().delete_room(id, data)


@socketio.on('reset_room')
def reset_room(id):
  global data

  Lobby().reset_room(id, data)


@socketio.on('generate-qrcode-pdf')
def generate_qrcode_pdf(context):
  global data

  content = Lobby().qrcode_iterator(context, data)
  pdf = PDF('P', 'mm', 'A4')
  output = pdf.generate_pdf(content['qrcodes'],
                   content['captions'])
  
  emit('get-qrcode-pdf',{'pdf': output})
  
  
  


@socketio.on('image')
def image(data_image):
  global data
  
  # temporaly tracking fluidity of the flux 
  # flux won't be further optimized, however frame interval each package is send can be modified
  config = data['config']
  odoo = Odoo()
  odoo.connect(config.API_URL, 
                  config.SERVICE_ACCOUNT_LOGGIN, 
                  config.SERVICE_ACCOUNT_PASSWORD, 
                  config.API_DB, 
                  config.API_VERBOSE)
  
  imageData = data_image['image']
  room_id = data_image['id']
  room = data['lobby']['rooms'][room_id]
  context = room.image_decoder(imageData, room_id, room, odoo, data)
  
  if context['state'] == 1:
    join_room(room_id)
    emit('move_product_to_queue', context, broadcast=True, include_self=True, to=room_id)
    emit('change_color', broadcast=False, include_self=True, to=room_id)
    emit('modify_scanned_item', context, broadcast=False, include_self=True, to=room_id)
  
  elif context['state'] == 2:
    emit('change_color', broadcast=False, include_self=True, to=room_id)

  
  


@socketio.on('laser')
def laser(data_laser):
  global data
  
  config = data['config']
  odoo = Odoo()
  odoo.connect(config.API_URL, 
                  config.SERVICE_ACCOUNT_LOGGIN, 
                  config.SERVICE_ACCOUNT_PASSWORD, 
                  config.API_DB, 
                  config.API_VERBOSE)

  room_id = data_laser['id']
  barcode = data_laser['barcode']
  room = data['lobby']['rooms'][room_id]
  context = room.laser_decoder(data_laser, room_id, barcode, room, odoo, data)
  
  if context['state'] == 1:
    join_room(room_id)
    emit('move_product_to_queue', context, broadcast=True, include_self=True, to=room_id)
    emit('modify_scanned_laser_item', context, broadcast=False, include_self=True, to=room_id)
    
  if context['state'] == 2:
    join_room(room_id)
    emit('already-scanned-alert', context, broadcast=False, include_self=True, to=room_id)




@socketio.on('update_table')
def get_update_table(context):
  global data
  from_table = context['table']
  room_id = context['roomID']
  room = data['lobby']['rooms'][room_id]

  if from_table == 'dataframe entry_table':
    context = room.update_table_on_edit(context)

  elif from_table == 'dataframe queue_table':
    context = room.update_table_on_edit(context)

  else: # done table
    context = room.update_table_on_edit(context)
  
  join_room(context['roomID'])
  emit('broadcast_update_table_on_edit', context, broadcast=True, include_self=True, to=context['roomID'])


@socketio.on('block-product')
def block_product(context):
  global data
  barcode = context['barcode']
  room_id = context['roomID']
  purchase = data['lobby']['rooms'][room_id].purchase
  purchase.append_new_items(barcode)

  emit('broadcast-block-wrong-item', context, broadcast=True, include_self=True)




@socketio.on('add-new-item')
def get_new_item(context):
  global data
  room_id = context['roomID']
  room = data['lobby']['rooms'][room_id]
  context = room.add_item(context)
  
  join_room(context['roomID'])
  emit('broadcasted_added_item', context, broadcast=True, include_self=False, to=context['roomID'])
  

@socketio.on('del_item')
def get_del_item(context):
  global data
  
  permission = task_permission_redirector(data, context)
  
  if permission:
    room_id = context['roomID']
    room = data['lobby']['rooms'][room_id]
    context = room.del_item(context)
    
    join_room(context['roomID'])
    emit('broadcasted_deleted_item', context, broadcast=True, include_self=True, to=context['roomID'])


@socketio.on('mod_item')
def get_mod_item(context):
  global data
  print(context)
  room_id = context['roomID']
  room = data['lobby']['rooms'][room_id]
  context = room.mod_item(context)
  
  join_room(context['roomID'])
  emit('broadcasted_mod_item', context, broadcast=True, include_self=True, to=context['roomID'])


@socketio.on('suspending_room')
def suspend_room(context):
  global data
  
  permission = task_permission_redirector(data, context)
  
  if permission:
    room_id = context['roomID']
    suffix = context['suffix']
    
    passer = get_passer(suffix)
    user_id = passer.get('id',None)
    token = passer.get('token',None)
    
    if not user_id or not token:
      url =  url_for('index')
      
    else:
      url = url_for('index_admin', id= user_id, token= token)


    Lobby().delete_room(room_id, data)

    context['url'] = url
    emit('broacasted_suspension', context, broadcast=True, include_self=True)


@socketio.on('finishing_room')
def finish_room(context):
  global data

  room_id = context['roomID']
  suffix = context['suffix']
  
  passer = get_passer(suffix)
  user_id = passer.get('id',None)
  token = passer.get('token',None)
  
  if not user_id or not token:
    url =  url_for('index')
    
  else:
    url = url_for('index_admin', id= user_id, token= token)


  room = data['lobby']['rooms'][room_id]
  room.update_status_to_received(data)

  context['url'] = url
  emit('broacasted_finish', context, broadcast=True, include_self=True)


@socketio.on('recharging_room')
def recharge_room(context):
  global data

  permission = task_permission_redirector(data, context)
  config = data['config']
  odoo = Odoo()
  odoo.connect(config.API_URL, 
                  config.SERVICE_ACCOUNT_LOGGIN, 
                  config.SERVICE_ACCOUNT_PASSWORD, 
                  config.API_DB, 
                  config.API_VERBOSE)
  
  if permission:
    room_id = context['roomID']
    purchase = data['lobby']['rooms'][room_id].purchase
    odoo.recharge_purchase(purchase, data)
    emit('reload-on-recharge', context, broadcast=False, include_self=True)
    emit('broadcast-recharge', context, broadcast=True, include_self=False)



@socketio.on('validation-purchase')
def validate_purchase(context):
  global data
  
  permission = task_permission_redirector(data, context)
  config = data['config']
  odoo = Odoo()
  odoo.connect(config.API_URL, 
                  config.SERVICE_ACCOUNT_LOGGIN, 
                  config.SERVICE_ACCOUNT_PASSWORD, 
                  config.API_DB, 
                  config.API_VERBOSE)
  
  if permission:
    print('____validation process______')
    room_id = context['roomID']
    suffix = context['suffix']
    room = data['lobby']['rooms'][room_id]
    purchase = room.purchase
    state = odoo.post_purchase(purchase, data)
    if state['validity']:
      room.update_status_to_verified(data)
      
      passer = get_passer(suffix)
      user_id = passer.get('id',None)
      token = passer.get('token',None)
      
      if not user_id or not token:
        url =  url_for('index')
        
      else:
        url = url_for('index_admin', id= user_id, token= token)      

        context['url'] = url
        emit('close-room-on-validation', context)
    
    else: 
      state['string_list'] = ', '.join(list(filter(lambda x: type(x) != bool, state['item_list'])))
      context['post_state'] = state
      emit('close-test-fail-error-window', context)