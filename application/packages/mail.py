import smtplib
from email.mime.text import MIMEText
from typing import List


### SEARCH PRODUCT
MULTI_ALT_BARCODE_PROB = """\
Lors de la reccherche d'un code-barre alternatif, l'application\
 a retrouver plusieurs produits correspondant. Un code-barre, devant être unique\
 l'application considère cela comme une anomalie.\
"""

MULTI_MAIN_BARCODE_PROB = """\
Lors de la reccherche du code-barre, l'application\
 a retrouver plusieurs produits correspondant. Un code-barre, devant être unique\
 l'application considère cela comme une anomalie.\
"""

MULTI_BARCODE_SOL = """\
Connecté vous à votre instance d'Odoo.\
 Dirigé vous vers l'onglet: ventes > articles > articles\n
 Inscriver le code barre du produit référencé plus haut dans ce mail.\
 Normalement plusieurs produits devraient être trouvés.\
 vérifié le code-barre et le code barre multiple (onglet) de ces produits\
 Modifié adéquatement le/les produits nécessaires\
 afin qu'il ne reste plus qu'un produit définis par le code-barre.\
"""

## VALIDATING 

ALREADY_VALIDATED_PROB = """\
La Commande/ Inventaire que vous souhaiter valider\
 à déjà été validée sur Odoo par un moyen alternatif.\n
Par concéquent, vous n'avez pas à la/ le valider sur l'application\
 L'application va automatiquement classifier cette commande comme validé cette nuit.\n
Vous n'avez rien à faire.\
"""

PRODUCT_NON_ODOO_EXIST = """\
Le(s) produit(s) préalablement listé(s) n'ont pas été trouvé(s) parmis les produits répertorié dans la base de donnée Odoo.\n
Il est nécessaire de rajouter la/ les fiches produits dans Odoo avant de pouvoir valider la commande.
"""

PRODUCT_NON_PURCHASE_EXIST = """\
Le(s) produit(s) préalablement listé(s) n'ont pas été trouvé(s) parmis les produits de la commande Odoo.\n
le paramètre: ODOO_CREATE_NEW_PURCHASE_LINE, étant désactivé,\
 l'application n'a pas l'autorisation pour ajouter automatiquement les produits manquants.\n
 Veuillez ajouter les produits manuellement dans la commande Odoo.
"""



class Mail(object):
  multi_prod_prob = "probs"
  multi_prod_sol = "sol"
  
  def __init__(self,
               tx: str, 
               pw: str, 
               port: int, 
               server: str, 
               rx: List[str]) -> None:
    
    self.tx = tx
    self.pw = pw
    self.port = port
    self.server = server
    self.rx = rx


  def write(self, context: dict) -> MIMEText:
    writer = getattr(self, context['mail_type'])
    msg = MIMEText(writer(context))
    msg['Subject'] = context['subject']
    msg['From'] = self.tx
    msg['To'] = ', '.join(self.rx)
    
    return msg

  def send(self, msg: MIMEText):
    with smtplib.SMTP(self.server, 
                      self.port) as smtp:
      smtp.login(self.tx, 
                 self.pw)
      smtp.starttls()
      smtp.sendmail(self.tx,
                    self.rx,
                    msg.as_string()) 
      
  def error_mail1(self, context: dict):    
    body = f"""\
    <font face="Courier New, Courier, monospace">
    <strong>Le scanner à rencontrer des anomalies sur la base de donnée Odoo</strong>\n
    <strong>Le salon et commande/inventaire concerné:</strong>\n
    {self.format_room(context['room'])}\n
    <strong>Le/les produit(s) concerné(s):</strong>\n
    {self.format_products(context['products'])}\n
    <strong>Le problème:</strong>
    {getattr(self,context['error_type'])}\n
    <strong>Démarche à suivre résoudre le problème:</strong>
    {getattr(self,context['error_solution'])}
    </font>"""

    return body
  
  def format_room(self, room:object):
    if room.name == '':
      name = room.id
    else:
      name = room.name
      
    s = f'{room.purchase.create_date} - {name} - {room.purchase.name} - {room.purchase.supplier.name}'
    return s
  
  def format_products(self, products:list):
    s = ""
    for p in products:
      s += f"{p.barcode} - {p.name} - {p.id}\n"
      
    return s

if __name__ == "__main__":
  pass
  # m = Mail(EMAIL_LOGIN,
  #          EMAIL_PASSWORD,
  #          SMTP_PORT,
  #          SMTP_SERVER,
  #          RECEIVERS)
  
  # msg = m.write({"body": "test test test", "error_type": "multi_prod_prob", "error_solution": "multi_prod_sol"}, "error_mail1", 'testing')
  # m.send(msg)
  