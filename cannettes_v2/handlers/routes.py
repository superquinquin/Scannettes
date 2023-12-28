from flask import Blueprint, render_template, request

from cannettes_v2.authenticator import Authenticator
from cannettes_v2.decorators import protected

cannettes_bp = Blueprint("cannettes_bp", __name__)


@cannettes_bp.route("/doc")
def doc():
    return render_template("doc.html")


@cannettes_bp.route("/login")
def login():
    return render_template("login.html")


@cannettes_bp.route("/setJWT", methods=["POST"])
def set_cookie():
    return Authenticator.login(request)


@cannettes_bp.route("/lobby")
def lobby():
    return render_template("lobby_v2.html")


@cannettes_bp.route("/admin/lobby")
@protected(auth_level="admin")
def admin_lobby():
    return render_template("lobby_admin_v2.html")


@cannettes_bp.route("/room/<tok>")
def room(tok):
    return render_template("room_v2.html")

@cannettes_bp.route("/admin/room/<tok>")
@protected(auth_level="admin")
def admin_room(tok):
    return render_template("room_admin_v2.html")





# @cannettes_bp.route(
#     "/lobby/admin/<id>&type=purchase&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>"
# )
# def get_purchase_room_admin(id, room_token, user_id, token, state):
#     return render_template("room_mobile.html")


# @cannettes_bp.route("/lobby/<id>&type=inventory&roomtoken=<room_token>")
# def get_inventory_room(id, room_token):
#     return render_template("room_inventory_mobile.html")


# @cannettes_bp.route(
#     "/lobby/admin/<id>&type=inventory&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>"
# )
# def get_inventory_room_admin(id, room_token, user_id, token, state):
#     return render_template("room_inventory_mobile.html")
