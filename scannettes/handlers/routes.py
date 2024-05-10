from flask import Blueprint, render_template, redirect, url_for, request, current_app

from scannettes.tools.authenticator import Authenticator
from scannettes.tools.decorators import protected

scannettes_bp = Blueprint("scannettes_bp", __name__)

@scannettes_bp.route("/doc")
def doc():
    return render_template("doc.html")


@scannettes_bp.route("/login")
def login():
    return render_template("login.html")


@scannettes_bp.route("/setJWT", methods=["POST"])
def set_cookie():
    return Authenticator.login(request)


@scannettes_bp.route("/lobby")
def lobby():
    authenticator = current_app.cache.config["authenticator"]
    if Authenticator.authorize(authenticator, request):
        return redirect(url_for("scannettes_bp.admin_lobby"))
    return render_template("lobby.html")


@scannettes_bp.route("/admin/lobby")
@protected(auth_level="admin")
def admin_lobby():
    return render_template("lobby.html")


@scannettes_bp.route("/room/<tok>")
def room(tok):
    return render_template("room.html")

@scannettes_bp.route("/admin/room/<tok>")
@protected(auth_level="admin")
def admin_room(tok):
    return render_template("room.html")


@scannettes_bp.route("/stock")
def stock():
    return render_template("stock.html")

@scannettes_bp.route("/stocks")
def stocks():
    return render_template("stocks.html")


@scannettes_bp.route("/getProduct", methods=["POST"])
def get_product():
    payload = request.json
    odoo = current_app.cache.inventories
    record = odoo.search_product_from_barcode(payload["barcode"])
    if record is None:
        return {"state": "err", "message": "Aucun produit trouvé correspondant à ce code-barres."}
    record = odoo.prepare_product_from_record(record)
    return {"state": "ok", "product": record}