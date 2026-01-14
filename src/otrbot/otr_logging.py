import logging
import logging.config
import sys

# Reconfigure stdout to use UTF-8 encoding for Hungarian characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

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
      "level": "DEBUG",
      "encoding": "utf-8"
    }
  },
  "formatters":{
    "std_out": {
      "format": "%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | %(lineno)d | %(thread)d, %(threadName)s | %(message)s",
      "datefmt":"%Y-%m-%d %I:%M:%S"
    }
  },
}

logging.config.dictConfig(log_config)
logger = logging.getLogger('OTR')