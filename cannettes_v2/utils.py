import os
import binascii
from glob import glob
from random import choices
from datetime import datetime, timedelta
from string import ascii_lowercase, ascii_uppercase, digits

from typing import Dict, Union, List, Any

ERROR_MESSAGES = {
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

def get_fix_delay(dtime:List[int]) -> float:
    H,M,S = dtime
    now = datetime.now()
    future = now.replace(hour=H, minute=M, second=S)
    if (future - now).total_seconds() < 0:
        future = future + timedelta(days=1)
    return (future - now).total_seconds()
    
def get_delay(dtime:List[int]) -> float:
    D,H,M,S = dtime
    now = datetime.now()
    future = now + timedelta(days=D, hours=H, minutes=M, seconds=S)
    return (future - now).total_seconds()


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
    return {"faulty_products": names, "error_message": ERROR_MESSAGES[payload["error_name"]]}


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
