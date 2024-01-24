import logging
from logging.handlers import RotatingFileHandler


class Logger(object):
    format = "%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s"
    level = "INFO"
    size = 5242880
    backup_count = 5
    
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.log = logging.getLogger("")
        self.log.setLevel(self.level)

        handler = self.log_handler()
        self.log.addHandler(handler)
        
        console = self.console_handler()
        self.log.addHandler(console)
        
        errors = self.error_log_handler()
        self.log.addHandler(errors)

    def log_handler(self):
        """base logger outputs"""
        handler = RotatingFileHandler(
            self.filename, 
            maxBytes=self.size, 
            backupCount=self.backup_count
        )
        formatter = logging.Formatter(self.format)
        handler.setLevel(self.level)
        handler.setFormatter(formatter)
        return handler
    
    def error_log_handler(self):
        """ERROR level logs"""
        handler = RotatingFileHandler(
            self.error_filename,
            maxBytes=0
        )
        formatter = logging.Formatter(self.format)
        handler.setLevel("ERROR")
        handler.setFormatter(formatter)
        return handler

    def console_handler(self):
        """base logger console stream"""
        console = logging.StreamHandler()
        console.setLevel(self.level)
        formatter = logging.Formatter(self.format)
        console.setFormatter(formatter)
        return console
