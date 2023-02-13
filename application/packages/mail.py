import smtplib
from email.mime.text import MIMEText
from typing import List


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


  def write(self, 
            context: dict, 
            mail_type: str, 
            subject: str) -> MIMEText:
    writer = getattr(self, mail_type)
    msg = MIMEText(writer(context))
    msg['Subject'] = subject
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
    return ''
  
  def format_products(self, products:list):
    return ''

if __name__ == "__main__":
  pass
  # m = Mail(EMAIL_LOGIN,
  #          EMAIL_PASSWORD,
  #          SMTP_PORT,
  #          SMTP_SERVER,
  #          RECEIVERS)
  
  # msg = m.write({"body": "test test test", "error_type": "multi_prod_prob", "error_solution": "multi_prod_sol"}, "error_mail1", 'testing')
  # m.send(msg)
  