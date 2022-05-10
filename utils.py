from datetime import datetime, timedelta


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



