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
    return render_template("lobby.html")


@cannettes_bp.route("/admin/lobby")
@protected(auth_level="admin")
def admin_lobby():
    return render_template("lobby.html")


@cannettes_bp.route("/room/<tok>")
def room(tok):
    return render_template("room.html")

@cannettes_bp.route("/admin/room/<tok>")
@protected(auth_level="admin")
def admin_room(tok):
    return render_template("room.html")