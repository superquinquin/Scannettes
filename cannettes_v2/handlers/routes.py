from flask import render_template
from flask import Blueprint


cannettes_bp = Blueprint('cannettes_bp', __name__)

@cannettes_bp.route("/doc")
def doc():
    return render_template("doc.html")

@cannettes_bp.route("/lobby")
def index():
    return render_template("lobby.html")

@cannettes_bp.route("/lobby&id=<id>&token=<token>")
def index_admin(id, token):
    return render_template("lobby.html")

@cannettes_bp.route("/lobby/login")
def login():
    return render_template("login.html")

@cannettes_bp.route("/lobby/<id>&type=purchase&roomtoken=<room_token>")
def get_purchase_room(id, room_token):
    return render_template("room_mobile.html")

@cannettes_bp.route("/lobby/admin/<id>&type=purchase&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>")
def get_purchase_room_admin(id, room_token, user_id, token, state):
    return render_template("room_mobile.html")

@cannettes_bp.route("/lobby/<id>&type=inventory&roomtoken=<room_token>")
def get_inventory_room(id, room_token):
    return render_template("room_inventory_mobile.html")

@cannettes_bp.route("/lobby/admin/<id>&type=inventory&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>")
def get_inventory_room_admin(id, room_token, user_id, token, state):
    return render_template("room_inventory_mobile.html")
