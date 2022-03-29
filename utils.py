def get_passer(suffix):
  passer = {}    
  for s in suffix.split('%26'):
    content = s.split('%3D')
    if len(content) == 2:
      passer[str(content[0])] = content[1]
  return passer