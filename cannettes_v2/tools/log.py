import logging
from logging.handlers import RotatingFileHandler


class Logger(object):
    format = "%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s"
    level = logging.INFO
    rotating = False
    size = 5242880
    backup_count = 5
    
    
    def __init__(self, **kwargs) -> None:

        self.__dict__.update(kwargs)
        if kwargs.get("level", None):
            self.level = getattr(logging, kwargs["level"])

        self.log = logging.getLogger("")
        self.log.setLevel(self.level)


        if self.rotating:
            handler = self.log_handler()
            self.log.addHandler(handler)
        
        console = self.console_handler()
        self.log.addHandler(console)


    def log_handler(self):
        handler = RotatingFileHandler(
            self.filename, 
            maxBytes=self.size, 
            backupCount=self.backup_count
        )
        formatter = logging.Formatter(self.format)
        handler.setLevel(self.level)
        handler.setFormatter(formatter)

        return handler

    def console_handler(self):
        console = logging.StreamHandler()
        console.setLevel(self.level)
        formatter = logging.Formatter(self.format)
        console.setFormatter(formatter)
        return console
