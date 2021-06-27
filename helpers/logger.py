import logging 
import sys

class CustomFormatter():
    """Logging Formatter to add colors and count warning / errors"""

    def __init__(self):
        
        self.grey = "\x1b[37m"
        self.yellow = "\x1b[33m"
        self.red = "\x1b[31m"
        self.bold_red = "\x1b[31;1m"
        self.reset = "\x1b[0m" 
        self.datefmt = "%B %d %Y %H:%M:%S"

        self.FORMATS_COLOR_MAPPING = {
            logging.DEBUG: self.grey,
            logging.INFO: self.grey,
            logging.WARNING: self.yellow,
            logging.ERROR: self.red,
            logging.CRITICAL: self.bold_red
        }
 
    def format(self, record):
        log_fmt_color = self.FORMATS_COLOR_MAPPING.get(record.levelno)
        log_fmt = "%(asctime)s - {log_color}%(levelname)s{color_reset} -  %(name)s - %(message)s".format(log_color=log_fmt_color, color_reset=self.reset)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)

class CustomLogger(object):
    _logger = None

    def __new__(cls, level=logging.DEBUG):
        if cls._logger is None:
            cls._logger = logging.getLogger('mumbleClient')
            # Create Console Output
            _handler = logging.StreamHandler(sys.stdout)
            # Add Custom Format to the Handler
            _handler.setFormatter(CustomFormatter())
            # Set Loglevel to the Desired One.
            _handler.setLevel(level)

            # Finally add the Handler to the Logger:
            cls._logger.addHandler(_handler)

            # Set the Log Level of the Logger.
            cls._logger.setLevel(level)
            
            # Put any initialization here.
        return cls._logger


def get_logger(name:str,level=logging.INFO):
    _logger = logging.getLogger(name)
    # Define  a Logging Format
    _format = _format = logging.Formatter(
        '%(asctime)s - %(levelname)s - '+name+' - %(message)s')
    # Create Console Output
    _handler = logging.StreamHandler(sys.stdout)
    # Add the Format to the Handler
    _handler.setFormatter(_format)
    # Set Loglevel to the Desired One.
    _handler.setLevel(level)

    # Finally add the Handler to the Logger:
    _logger.addHandler(_handler)

    # Set the Log Level of the Logger.
    _logger.setLevel(level)
    return _logger
