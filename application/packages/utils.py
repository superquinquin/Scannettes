import pandas as pd
from typing import Union
from dateutil.relativedelta import *
from datetime import datetime, timedelta
import argparse
from config import configDict


def get_passer(suffix):
  passer = {}    
  for s in suffix.split('%26'):
    content = s.split('%3D')
    if len(content) == 2:
      passer[str(content[0])] = content[1]
  return passer



def get_delay(**kwargs):

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

  Y, M, W, D = timeDelta[0], timeDelta[1], timeDelta[2], timeDelta[3] # YEAR, MONTH, WEEK, DAY

  if not data['odoo']['history'][key]:
    date_ceiling = (datetime.now().date() + 
                    relativedelta(years=-Y ,months=-M, weeks=-W, days=-D)).strftime("%Y-%m-%d %H:%M:%S")
  else:
    date_ceiling = data['odoo']['history'][key][-1]

  return date_ceiling



def update_item_auto_table_selector(purchase, productData: dict, state: Union[None, str], item_state: str) -> None:
  """
  Update tables.
  """
  passed = False
  # update purchase.table
  if item_state != 'cancel':
    passed = purchase.update_item('table', 'id', productData['item_id'], productData, passed)
    passed = purchase.update_item('table', 'barcode', productData['item_barcode'], productData, passed)

    if passed == False:
      passed = purchase.create_item(purchase.table, productData)
  
  else:
    passed = purchase.delete_item('table', 'id', productData['item_id'], passed)
    passed = purchase.delete_item('table', 'barcode', productData['item_barcode'], passed)


  if state is not None:
    passed = False
    # then purchase.table is divided in entries, queue and done tables
    if item_state != 'cancel':
      passed = purchase.update_item('purchased', 'id', productData['item_id'], productData, passed)
      passed = purchase.update_item('purchased', 'barcode', productData['item_barcode'], productData, passed)

      passed = purchase.update_item('done', 'id', productData['item_id'], productData, passed)
      passed = purchase.update_item('done', 'barcode', productData['item_barcode'], productData, passed)

      passed = purchase.update_item('queue', 'id', productData['item_id'], productData, passed)
      passed = purchase.update_item('queue', 'barcode', productData['item_barcode'], productData, passed)

      if passed == False:
        passed = purchase.create_item(purchase.table_entries, productData)

    else:
      passed = purchase.delete_item('purchased', 'id', productData['item_id'], passed)
      passed = purchase.delete_item('purchased', 'barcode', productData['item_barcode'], passed)

      passed = purchase.delete_item('done', 'id', productData['item_id'], passed)
      passed = purchase.delete_item('done', 'barcode', productData['item_barcode'], passed)

      passed = purchase.delete_item('queue', 'id', productData['item_id'], passed)
      passed = purchase.delete_item('queue', 'barcode', productData['item_barcode'], passed)



def define_config(config_name: Union[None, str]=None):
  if config_name is None:
    config = configDict['dev']
  
  else:
    config = configDict[config_name]
  
  return config


def parser():
  parser = argparse.ArgumentParser(description='choose config')
  parser.add_argument('--config', choices=['dev', 'staging', 'production'],
                      help= 'add config setup dev, staging or production')
  args = parser.parse_args()

  return args