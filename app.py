import time
from flask import Flask, url_for, render_template
from flask_socketio import SocketIO, emit, send, join_room, leave_room

from config import config
from classes import data, Odoo, Purchase, Lobby, Room, User, Log  



app = Flask(__name__,
            static_url_path= config['static_url'])
socketio = SocketIO(app, 
                    cors_allowed_origins= config['allowed_origins'])


t = []


# route
@app.route('/lobby')
def index():
  return render_template('lobby.html')

@app.route('/lobby&id=<id>')
def index_admin(id):
  return render_template('lobby.html')


@app.route('/lobby/login')
def login():
  return render_template('login.html')


@app.route('/lobby/<id>')
def get_room(id):
  return render_template('room.html')

@app.route('/lobby/admin/<id>')
def get_room_admin(id):
  return render_template('room.html')



# call
@socketio.on('message')
def handle_my_custom_event(msg):
  print(str(msg))


@socketio.on('ask_permission')
def verify_loggin(context):
  global data

  permission = False
  url = ''

  id = context['id']
  password = context['password']
  whitelist = open(config['whitelist'], 'r', encoding='utf-8', errors='ignore')

  for identifier in whitelist.readlines():
    i = identifier.split()
    if id == i[0] and password == i[1]:
      permission = True
      data['lobby']['users']['admin'][id] = User(id, 'lobby', permission)
      url = url_for('index_admin', id= id)
      break

  print(data['lobby']['users']['admin'][id].id)
  emit('permission', {'permission': permission, 'user_id': id, 'url': url}, include_self=True)


@socketio.on('verify_connection')
def verify_logger(id):
  global data

  permission = False

  for user_id in data['lobby']['users']['admin'].keys():
    user = data['lobby']['users']['admin'][user_id]
    if user.id == id and user.session == 1:
      emit('grant_permission', {'permission': permission})
  







@socketio.on('redirect')
def redirect(context):
  global data

  id = context['id']
  password = context['password']
  index = context['index']
  suffix = context['suffix']
  room_password = data['lobby']['rooms'][id].password
  if password == room_password:
    if suffix == 'lobby':
      emit('go_to_room', {'url': url_for('get_room', id=id)})
    else:
      for k in data['lobby']['users']['admin'].keys():
        user_id = k
        user_session = data['lobby']['users']['admin'][k].session
        user_loc = data['lobby']['users']['admin'][k].location
        if suffix == user_id and user_session == 1 and user_loc == 'lobby':
          emit('go_to_room', {'url': url_for('get_room_admin', id=id+'&id='+user_id)})
          break
  else:
    emit('access_denied', index,include_self=True)


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

  context = {'room_id': id,
             'room_name': name,
             'purchase_name': purchase,
             'entries_table':html_ent,
             'queue_table':html_quet,
             'done_table':html_dont}
  
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
  
  emit('add_room', input, broadcast=True, include_self=True,)


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
  room.barcode_decoder(imageData, room_id, room, odoo)



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





if __name__ == '__main__':
  app.jinja_env.auto_reload = True
  app.config['TEMPLATES_AUTO_RELOAD'] = True


  odoo = Odoo()
  lobby = Lobby()
  odoo.build(config['url'], config['login'], config['password'], config['db'], config['verbose'], config['timeDelta'])
  print(data['odoo'])

  socketio.run(app)
  #http://localhost:5000/lobby
