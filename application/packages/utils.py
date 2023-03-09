import os
import binascii
import pandas as pd
from glob import glob
from typing import Dict, Union, Tuple, List
from dateutil.relativedelta import *
from datetime import datetime, timedelta




def generate_token(size:int):
  """generate hex token of size "size" """
  return binascii.hexlify(os.urandom(size)).decode()  


def get_passer(suffix:str) -> dict:
  """decompose suffix str into args"""
  passer = {}    
  for s in suffix.split('%26'):
    content = s.split('%3D')
    if len(content) == 2:
      passer[str(content[0])] = content[1]
  return passer

def get_task_permission(data: dict, suffix: str) -> bool:
  """
  unpack suffix
  from connection suffix, 
  give permission or not
  """
  permission = False
  
  passer = get_passer(suffix)
  id = passer.get('id',None)
  token = passer.get('token',None)
  state = passer.get('state',None)
  
  user = data['lobby']['users']['admin'].get(id, None)
  if user:
    permission = user.verify_permision(token)
  
  return permission

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
  delta = kwargs.get('delta', None)
  time = kwargs.get('time', None)

  if time:
    # daily
    h,m,s = time[0], time[1], time[2]
    launch = now.replace(hour=h, minute=m, second=s, microsecond=0)
    delay = (launch - now).total_seconds()

    if delay < 0:
      delayed = 0

      while delay < 0:
        next_start = now.replace(hour=h, minute=m, second=s, microsecond=0) + timedelta(days= delayed)
        delay = (next_start - now).total_seconds()
        delayed += 1
        print(next_start)

      else:
        delay = (next_start - now).total_seconds()

  elif delta:
    # based on defined frequence
    D, H, M, S = delta[0], delta[1], delta[2], delta[3]

    next_start = now + timedelta(days= D, hours= H,minutes= M,seconds= S)
    delay = (next_start - now).total_seconds()
  
  else:
    raise KeyError("You must at least define kwargs time or delta")

  return delay


def get_ceiling_date(timeDelta: list, data: dict, key: str) -> str:
  """provide a ceiling date for purchase search
  wether a search historic exist, then take last search as ceiling
  otherwise take timedelta from config file

  Args:
      timeDelta (list): list of YEAR, MONTH, WEEK, DAY  as int
      data (dict): cache dict
      key (str): key of history field , kinda irrelevant now that inventory are not search at all

  Returns:
      str: date a str
  """
  Y, M, W, D = timeDelta[0], timeDelta[1], timeDelta[2], timeDelta[3] # YEAR, MONTH, WEEK, DAY

  if data['odoo']['history'][key] and data['config'].ENV == 'production':
    date_ceiling = data['odoo']['history'][key][-1]
    
  else:
    date_ceiling = (datetime.now().date() + 
                relativedelta(years=-Y ,months=-M, weeks=-W, days=-D)).strftime("%Y-%m-%d %H:%M:%S")

  return date_ceiling


def is_too_old(date:object, ceiling:int) -> bool:
  """look if date is < a ceiling date

  Args:
      date (object): datetime object
      ceiling (int): ceiling delta in sec

  Returns:
      bool: if date < ceiling date
  """
  now = datetime.now()
  delta = int((now - datetime.strptime(date, '%Y-%m-%d %H:%M:%S')).total_seconds())
  
  if delta > ceiling:
    return True
  else:
    return False
  

def standart_name(name: str, id:str) -> str:
  """standardise name or replace it by id"""
  if name == '':
    return id
  else:
    return name
  
def standart_object_name(id: Union[str, int, None], supplier: str) -> str:
  """ standardise object name"""
  if type(id) == int:
    id = f'PO0{str(id)}'
  if not id or 'spo' in id:
    id = 'aucune'
  else:
    id = f'{str(id)} - {supplier}'
    
  return id
    
def get_status_related_collections(atype:str, new_status:str) -> Tuple[str, str]:
  """provide status duo regarding type of object

  Args:
      atype (str): type of the object (inventory or purchase)
      new_status (str): updating status

  Returns:
      Tuple[str, str]: tuple of status to complete status changes regarding type of object
  """
  if atype == "inventory" and new_status == "finished":
    return "ongoing", "processed"
  elif atype == "inventory" and new_status == "verified":
    return "processed", "done"
  elif atype == "purchase" and new_status == "finished":
    return "incoming", "received"
  elif atype == "purchase" and new_status == "verified":
    return "received", "done"
  
  
def order_files(files: List[str]) -> List[str]:
  """give order for unifying process"""
  ordered, schema = [], ['config', 'init', 'functions', 'product', 'camera', 'others']
  for t in schema:
    for file in files:
      if t in file:
        ordered.append(file)
      if t == "others" and file not in ordered:
        ordered.append(file)
  
  return ordered
  
def unify(folder:str, types:str, outfile:str) -> None:
  """unify folder files into an unified file
  this aim to limit client request as page open"""
  glob_files = glob(f'{"/".join(folder.split("/")[:-1])}/*.{types}')
  files = glob(f'{folder}/*.{types}')
  ordered = order_files(glob_files + files)
  with open(f'{folder}/{outfile}.{types}','w') as unify:
    for file in ordered:
      if ("inventory" in outfile and
          "purchase" in file):
        continue
      
      elif ("purchase" in outfile and
          "inventory" in file):
        continue
      
      elif "unified" in file:
        continue
      
      else:
        with open(file, 'r') as f:
          content = f.read()
          unify.write(f'{content}\n')

          
def format_error_cases(channel:str, context: dict):
  # channel [item_validity, unmatch]
  
  if channel == 'unmatch':
    if context['barcode'] == False:
      ## no barcode
      hint = "Aucun code-barres associés à ce produit dans Odoo"
      err = "NoBarcode"
    else:
      ## ID AND BARCODE DO NOT MATCH IN CHECK PROCESS
      hint = "Le code-barres ne correspond pas au bon produit Odoo"
      err = "NoMatchs"
  
  elif channel == "item_validity":
    if context['alt'] == None and context['has_main'] == False:
      hint = "Le produit n'est pas référencé dans Odoo"
      err = "NoExist"
    elif context['alt'] != None and context['has_main'] == True:
      hint = "Le code-barres est à la fois un code-barre principale et multiple"
      err = "MultiOccur"
    elif context['alt'] != None and context['has_main'] == False:
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
  
  return {"barcode": context['barcode'],
          "product": context['product'],
          "hint": hint,
          "err": err}

def format_error_client_message(errors:List[dict]) -> str:
  """takes context from failed process like odoo post process
format the errors component into string to be displayed into the client

  Args:
      errors (List): list of object err with keys: barcode, product, hint

  Returns:
      str: formated string
  """
  
  s = ""
  for err in errors:
    if err['barcode'] != False and err['product'] != None:
      s += f"&#8226; {err['barcode']}, {err['product'].name} ({err['hint']}),<br>"
    elif err['barcode'] == False and err['product'] != None:
      s += f"&#8226; {err['product'].name} ({err['hint']}),<br>"
    elif err['barcode'] == False and err['product'] == None:
      s += f"&#8226; produit inconnu ({err['hint']}),<br>"
    elif err['barcode'] != False and err['product'] == None:
      s += f"&#8226; {err['barcode']} ({err['hint']}),<br>"
  
  return s.rstrip(',<br>')