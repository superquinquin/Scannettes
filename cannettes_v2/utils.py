import os
import json
import binascii
from glob import glob
from typing import Dict, Union, Tuple, List, Any
from dateutil.relativedelta import *
from datetime import datetime, timedelta
from string import ascii_lowercase, ascii_uppercase, digits
from random import choices

error_messages = {
    "odoout": "Les produits suivant ne sont pas référencés dans Odoo. Veuillez les ajouter ou les supprimer de l'application.",
    "purout": "Les produits suivant n'ont pas été commandés. Veuillez les ajouter dans le bon de commande Odoo ou activer l'option pour que l'application rajoute automatiquement les produits.",
    "odostockinvfail": "Les produits suivant ne peuvent être ajouté à l'inventaire. Vérifiez sur Odoo qu'ils ne sont pas déjà dans un autre inventaire."
}



CHARS = ascii_lowercase + ascii_uppercase + digits

def generate_uuid() -> str:
    """fewer collisions method"""
    return ''.join(choices(CHARS, k=8))

def generate_token(size: int):
    """generate hex token of size "size" """
    return binascii.hexlify(os.urandom(size)).decode()


def get_update_time_ceiling(last_update: datetime, delta: List[int]) -> datetime:
    ceiling = last_update
    if ceiling is None:
        Y, M, W, D = delta
        now = datetime.now().date()
        ceiling = now + timedelta(weeks= -W, days= -D)
        ceiling = ceiling.strftime("%Y-%m-%d %H:%M:%S")
    return ceiling

def get_best_state(states: List[str]) -> str:
    """used for stock.move ; stock.picking status system"""
    status = {"cancel": 0, "assigned": 1, "done": 2}
    return max([(s, status.get(s)) for s in states], key= lambda x: x[1])[0]


def update_object(cls: object, payload: Dict[str, Any]) -> None:
    for k, v in payload.items():
        current = getattr(cls, k, None)
        if current is None:
            raise KeyError(f"{cls} : {k} attribute doesn't exist")
        if type(current) != type(v) and current is not None:
            raise TypeError(
                f"{cls} : field {k} value {v} ({type(v)}) does not match current type ({type(current)})"
            )
        setattr(cls, k, v)

def restrfmtdate(date:Union[None, str]) -> str:
    if date is None:
        return date
    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    return date.strftime("%d/%m/%Y")


def get_delay(**kwargs) -> int:
    """provide delay between 2 timed threads
    accepted args:
      delta: list of int: stand for a delay between 2 threads
      time: list of int: stand for a daily fixed hour

    Raises:
        KeyError: must define a time or a delta

    Returns:
        _type_: delay in sec
    """
    now = datetime.now()
    delta = kwargs.get("delta", None)
    time = kwargs.get("time", None)

    if time:
        # daily
        h, m, s = time[0], time[1], time[2]
        launch = now.replace(hour=h, minute=m, second=s, microsecond=0)
        delay = (launch - now).total_seconds()

        if delay < 0:
            delayed = 0

            while delay < 0:
                next_start = now.replace(
                    hour=h, minute=m, second=s, microsecond=0
                ) + timedelta(days=delayed)
                delay = (next_start - now).total_seconds()
                delayed += 1
                print(next_start)

            else:
                delay = (next_start - now).total_seconds()

    elif delta:
        # based on defined frequence
        D, H, M, S = delta[0], delta[1], delta[2], delta[3]

        next_start = now + timedelta(days=D, hours=H, minutes=M, seconds=S)
        delay = (next_start - now).total_seconds()

    else:
        raise KeyError("You must at least define kwargs time or delta")

    return delay


def is_too_old(date: datetime, ceiling: int) -> bool:
    """check if time delta > ceiling in sec"""
    return int((datetime.now() - datetime.strptime(date, "%Y-%m-%d %H:%M:%S")).total_seconds()) > ceiling


def build_validation_error_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    names = []
    for p in payload["failing"]:
        name = f"Produit inconnu ({p.barcodes[0]})"
        if p.pid:
            name += f"{p.pid} - {p.name} ({p.barcodes[0]})"
        names.append(name)
    return {"faulty_products": names, "error_message": error_messages[payload["error_name"]]}


    
























































def order_files(files: List[str]) -> List[str]:
    """give order for unifying process"""
    ordered, schema = [], ["config", "init", "functions", "product", "camera", "others"]
    for t in schema:
        for file in files:
            if t in file:
                ordered.append(file)
            if t == "others" and file not in ordered:
                ordered.append(file)

    return ordered


def unify(folder: str, types: str, outfile: str) -> None:
    """unify folder files into an unified file
    this aim to limit client request as page open"""
    glob_files = glob(f'{"/".join(folder.split("/")[:-1])}/*.{types}')
    files = glob(f"{folder}/*.{types}")
    ordered = order_files(glob_files + files)
    with open(f"{folder}/{outfile}.{types}", "w") as unify:
        for file in ordered:
            if "inventory" in outfile and "purchase" in file:
                continue

            elif "purchase" in outfile and "inventory" in file:
                continue

            elif "unified" in file:
                continue

            else:
                with open(file, "r") as f:
                    content = f.read()
                    unify.write(f"{content}\n")




def format_error_cases(channel: str, context: dict):
    # channel [item_validity, unmatch]

    if channel == "unmatch":
        if context["barcode"] == False:
            ## no barcode
            hint = "Aucun code-barres associés à ce produit dans Odoo"
            err = "NoBarcode"
        else:
            ## ID AND BARCODE DO NOT MATCH IN CHECK PROCESS
            hint = "Le code-barres ne correspond pas au bon produit Odoo"
            err = "NoMatchs"

    elif channel == "item_validity":
        if context["alt"] == None and context["has_main"] == False:
            hint = "Le produit n'est pas référencé dans Odoo"
            err = "NoExist"
        elif context["alt"] != None and context["has_main"] == True:
            hint = "Le code-barres est à la fois un code-barre principale et multiple"
            err = "MultiOccur"
        elif context["alt"] != None and context["has_main"] == False:
            hint = "Le code-barre n'a pas de produits principaux"
            err = "OnlyALt"

    elif channel == "creation_no_exist":
        hint = "Le produit n'est pas référencé dans Odoo"
        err = "CreationNoExist"

    elif channel == "creation_inactivated":
        hint = "La création automatique de produit est désactivée"
        err = "CreationInactivated"

    elif channel == "inv_block":
        hint = "Déjà dans un inventaire en cours"
        err = "multiInvOpen"

    return {
        "barcode": context["barcode"],
        "product": context["product"],
        "hint": hint,
        "err": err,
    }


def format_error_client_message(errors: List[dict]) -> str:
    """takes context from failed process like odoo post process
    format the errors component into string to be displayed into the client

      Args:
          errors (List): list of object err with keys: barcode, product, hint

      Returns:
          str: formated string
    """

    s = ""
    for err in errors:
        if err["barcode"] != False and err["product"] != None:
            s += f"&#8226; {err['barcode']}, {err['product'].name} ({err['hint']}),<br>"
        elif err["barcode"] == False and err["product"] != None:
            s += f"&#8226; {err['product'].name} ({err['hint']}),<br>"
        elif err["barcode"] == False and err["product"] == None:
            s += f"&#8226; produit inconnu ({err['hint']}),<br>"
        elif err["barcode"] != False and err["product"] == None:
            s += f"&#8226; {err['barcode']} ({err['hint']}),<br>"

    return s.rstrip(",<br>")
