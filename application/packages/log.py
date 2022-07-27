import sys
import os
import logging
from logging.handlers import RotatingFileHandler


class Log:
  def __init__(self, config) -> None:
    self.env = config.ENV
    
    # self.mkdir(config)
    
    self.log = logging.getLogger('')
    self.log.setLevel(logging.DEBUG)
    
    handler = self.log_handler(config)
    console = self.console_handler()

    self.log.addHandler(console)
    self.log.addHandler(handler)


  def mkdir(self, config):
    folder_name = '/'.join(config.LOG_FILENAME.split('/')[:-1])
    print(folder_name)
    if not os.path.exists(folder_name):
      os.makedirs('./log')


  def log_handler(self, config):
    handler = RotatingFileHandler(config.LOG_FILENAME, maxBytes=5*1024*1024,
                                  backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter) 
    
    return handler
  
  
  def console_handler(self):
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
    console.setFormatter(formatter)
    
    return console    


class Hook:
  def __init__(self):
    self.log = logging.getLogger('exceptionHook')
    
  def exception_hook(self, exc_type, exc_value, tb):
    
    self.log.error("Uncaught exception", exc_info=(exc_type, exc_value, tb))



class ErrLogFlush:
  def __init__(self, config):
    self.console = sys.stderr
    self.file = open(config.LOG_FILENAME, 'a')

  def write(self, message):
    self.console.write(message)
    self.file.write(message)
 
  def flush(self):
    self.console.flush()
    self.file.flush()   


