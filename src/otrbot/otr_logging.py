import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path

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
      # One file per run, so a restarted run does not overwrite the log of the previous one
      "filename": f"./logs/otr_{datetime.now():%Y%m%d_%H%M%S}.log",
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

Path("./logs").mkdir(exist_ok=True)
logging.config.dictConfig(log_config)
logger = logging.getLogger('OTR')