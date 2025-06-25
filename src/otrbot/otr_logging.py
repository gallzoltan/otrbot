import logging
from logging import config

log_config = {
  "version":1,
  "root":{
    "handlers" : ["console", "file"],
    "level": "DEBUG"
  },
  "handlers":{
    "console":{
      "formatter": "std_out",
      "class": "logging.StreamHandler",
      "level": "DEBUG"
    },        
    "file":{
      "formatter": "std_out",
      "class": "logging.FileHandler",
      "filename": "./logs/otr.log",
      "mode":"w",
      "level": "DEBUG"
    }        
  },
  "formatters":{
    "std_out": {
      "format": "%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | %(lineno)d | %(thread)d, %(threadName)s | %(message)s",
      "datefmt":"%Y-%m-%d %I:%M:%S"
    }
  },
}

config.dictConfig(log_config)
logger = logging.getLogger('OTR')

# _formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
# _handlers = [logging.StreamHandler(), logging.FileHandler('./logs/file.log', mode='w')]
# logger = logging.getLogger('OTR')
# for handler in _handlers:
#   handler.setFormatter(_formatter)
#   logger.addHandler(handler)  
# logger.setLevel(logging.DEBUG)