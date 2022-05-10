import time
from flask import Flask, url_for, render_template, request
from flask_socketio import SocketIO, emit, send, join_room, leave_room

from config import config
from classes import data, Odoo, Purchase, Lobby, Room, User, Log, BackUp
from utils import get_passer



app = Flask(__name__,
            static_url_path= config['static_url'])
socketio = SocketIO(app, 
                    cors_allowed_origins= config['allowed_origins'])


t = []


# route
@app.route('/lobby')
def index():
  return render_template('lobby.html')

@app.route('/lobby&id=<id>&token=<token>')
def index_admin(id, token):
  return render_template('lobby.html')


@app.route('/lobby/login')
def login():
  return render_template('login.html')


@app.route('/lobby/<id>')
def get_room(id):
  # return render_template('room.html')
  return render_template('room_mobile.html')


@app.route('/lobby/admin/<id>&id=<user_id>&token=<token>&state=<state>')
def get_room_admin(id, user_id, token, state):
    # return render_template('room.html')
  return render_template('room_mobile.html')



# call
@socketio.on('message')
def handle_my_custom_event(msg):
  print(str(msg))


@socketio.on('ask_permission')
def verify_loggin(context):
  global data

  print(request.remote_addr)
  print(request.environ['REMOTE_ADDR'])
  if request.environ.get('HTTP_X_FORWARDED_FOR'):
    print(request.environ['HTTP_X_FORWARDED_FOR'])
  else:
    print(request.environ.get('HTTP_X_FORWARDED_FOR'))

  permission = False
  url = ''

  id = context['id']
  password = context['password']
  browser_id = context['browser']
  whitelist = open(config['whitelist'], 'r', encoding='utf-8', errors='ignore')

  for identifier in whitelist.readlines():
    i = identifier.split()
    if id == i[0] and password == i[1]:
      permission = True
      data['lobby']['users']['admin'][id] = User(id, 'lobby', browser_id, permission)
      token = data['lobby']['users']['admin'][id].token
      url = url_for('index_admin', id= id, token= token)
      break

  print(data['lobby']['users']['admin'][id].id)
  emit('permission', {'permission': permission, 'user_id': id, 'url': url}, include_self=True)


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

  if user_id in data['lobby']['users']['admin'].keys():
    user = data['lobby']['users']['admin'][user_id]

    if user.token == token and user.browser_id == browser_id:    
      emit('grant_permission', {'permission': permission})
  







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


  if password == room.password:

    if suffix == 'lobby':
      emit('go_to_room', {'url': url_for('get_room', id=id)})

    else:
      user_id = passer.get('id',None)

      if user_id in data['lobby']['users']['admin'].keys():
        user = data['lobby']['users']['admin'][user_id]
        token = passer.get('token',None)

        if user.token == token and user.browser_id == browser:
            emit('go_to_room', {'url': url_for('get_room_admin', id= id, user_id= user_id, token= token, state= room.status, winWidth=winWidth)})
        
        else:
          emit('go_to_room', {'url': url_for('get_room', id=id)})
      
      else:
        emit('go_to_room', {'url': url_for('get_room', id=id)})

  else:
    emit('access_denied', context,include_self=True)


@socketio.on('join_lobby')
def join_lobby():
  global data
  print('joining lobby')

  context = {'room': [],
             'selector': []}

  for k in data['lobby']['rooms'].keys():
    id = data['lobby']['rooms'][k].id
    name = data['lobby']['rooms'][k].name
    status = data['lobby']['rooms'][k].status
    date = data['lobby']['rooms'][k].oppening_date
    purchase_name = data['lobby']['rooms'][k].purchase.name

    context['room'].append([id, name, purchase_name, status, date])
  
  for k in data['odoo']['purchases']['incoming'].keys():
    id = data['odoo']['purchases']['incoming'][k].id
    name = data['odoo']['purchases']['incoming'][k].name
    context['selector'].append(tuple((id, name)))
  
  emit('load_existing_lobby', context, include_self=True)


@socketio.on('join_room')
def join_room(room):
  global data

  room = data['lobby']['rooms'][room]
  name = room.name
  id = room.id
  purchase = room.purchase.name

  html_ent, html_quet, html_dont = room.purchase.table_position_to_html()
  entry_records, queue_records, done_records = room.purchase.get_table_records()


  context = {'room_id': id,
             'room_name': name,
             'purchase_name': purchase,
             'entries_table':html_ent,
             'queue_table':html_quet,
             'done_table':html_dont,
             'entries_records': entry_records,
             'queue_records': queue_records,
             'done_records': done_records,
             'scanned': room.purchase.scanned_barcodes,
             'new': room.purchase.new_items,
             'mod': room.purchase.modified_items}
  
  emit('load_existing_room', context)


@socketio.on('create_room')
def create_room(input):
  global data, lobby
  print('create room')

  room = lobby.create_room(input)

  input['status'] = room.status
  input['users'] = room.users
  input['creation_date'] = room.oppening_date
  if room.purchase.process_status == None:
    room.purchase.build_process_tables()
  
  emit('add_room', input, broadcast=True, include_self=True)


@socketio.on('del_room')
def del_room(id):
  global lobby
  lobby.delete_room(id)


@socketio.on('reset_room')
def reset_room(id):
  global lobby
  print(id)
  lobby.reset_room(id)



@socketio.on('image')
def image(data_image):
  global data, odoo, t 
  
  # temporaly tracking fluidity of the flux 
  # flux won't be further optimized, however frame interval each package is send can be modified
  if t:
    t.append(time.time())
    print(t[1] - t[0])
    t.pop(0)
  else:
    t.append(time.time())

  imageData = data_image['image']
  room_id = data_image['id']
  room = data['lobby']['rooms'][room_id]
  room.image_decoder(imageData, room_id, room, odoo)


@socketio.on('laser')
def laser(data_laser):
  global data, odoo

  room_id = data_laser['id']
  barcode = data_laser['barcode']
  room = data['lobby']['rooms'][room_id]
  room.laser_decoder(data_laser, room_id, barcode, room, odoo)





@socketio.on('update_table')
def get_update_table(context):
  global data
  from_table = context['table']
  room_id = context['roomID']
  room = data['lobby']['rooms'][room_id]

  if from_table == 'dataframe entry_table':
    room.update_table_on_edit(context)

  elif from_table == 'dataframe queue_table':
    room.update_table_on_edit(context)

  else: # done table
    room.update_table_on_edit(context)


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
  room.add_item(context)
  

@socketio.on('del_item')
def get_del_item(context):
  global data
  room_id = context['roomID']
  room = data['lobby']['rooms'][room_id]
  room.del_item(context)


@socketio.on('mod_item')
def get_mod_item(context):
  global data
  print(context)
  room_id = context['roomID']
  room = data['lobby']['rooms'][room_id]
  room.mod_item(context)


@socketio.on('suspending_room')
def suspend_room(context):
  global data, lobby

  room_id = context['roomID']
  suffix = context['suffix']

  if suffix == room_id:
    url =  url_for('index')

  else:
    passer = get_passer(suffix)
    user_id = passer.get('id',None)
    token = passer.get('token',None)
    url = url_for('index_admin', id= user_id, token= token)

  lobby.delete_room(room_id)

  context['url'] = url
  emit('broacasted_suspension', context, broadcast=True, include_self=True)


@socketio.on('finishing_room')
def finish_room(context):
  global data, lobby

  room_id = context['roomID']
  suffix = context['suffix']

  if suffix == room_id:
    url =  url_for('index')

  else:
    passer = get_passer(suffix)
    user_id = passer.get('id',None)
    token = passer.get('token',None)
    url = url_for('index_admin', id= user_id, token= token)

  room = data['lobby']['rooms'][room_id]
  room.update_status_to_received()

  context['url'] = url
  emit('broacasted_finish', context, broadcast=True, include_self=True)


@socketio.on('recharging_room')
def recharge_room(context):
  global data, odoo

  room_id = context['roomID']
  suffix = context['suffix']
  purchase = data['lobby']['rooms'][room_id].purchase
  odoo.recharge_purchase(purchase)
  emit('reload-on-recharge', context, broadcast=False, include_self=True)
  emit('broadcast-recharge', context, broadcast=True, include_self=False)



@socketio.on('validation-purchase')
def validate_purchase(context):
  global data, odoo

  print('____validation process______')
  room_id = context['roomID']
  suffix = context['suffix']
  room = data['lobby']['rooms'][room_id]
  state = odoo.post_purchase(room)
  room.update_status_to_verified()

  if suffix == room_id:
    url =  url_for('index')

  else:
    passer = get_passer(suffix)
    user_id = passer.get('id',None)
    token = passer.get('token',None)
    url = url_for('index_admin', id= user_id, token= token)

  

  context['url'] = url
  emit('close-room-on-validation', context)













if __name__ == '__main__':
  app.jinja_env.auto_reload = True
  app.config['TEMPLATES_AUTO_RELOAD'] = True


  odoo = Odoo()
  lobby = Lobby()
  if config['build_on_backup']: 
    data = BackUp.load_backup(config['backup_fileName'])
  odoo.build(config['url'], config['login'], config['password'], config['db'], config['verbose'], config['timeDelta'])
  BackUp().BACKUP_RUNNER()
  odoo.UPDATE_RUNNER()

  socketio.run(app)
  #http://localhost:5000/lobby

