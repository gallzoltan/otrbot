import sys
import argparse
import otrbot.otr_logging as logging
from pathlib import Path
from dotenv import load_dotenv
from otrbot.constants import WebDriverConfig
from otrbot.runner import ModuleRunner
from otrbot.config import Config


def validate_arguments(args) -> bool:
  """Validate command line arguments"""
  if not Path(args.file).exists():
    logging.logger.error(f"File not found: {args.file}")
    return False
  
  if args.supporter not in ["BM", "KTM"]:
    logging.logger.error(f"Invalid supporter: {args.supporter}")
    return False
      
  return True

def get_driver_options():
  # "--window-size=1100,1080",
  # "--start-maximized",
  # "--disable-gpu",   
  # "--disable-dev-shm-usage",
  # "--disable-popup-blocking",    
  # "--disable-software-rasterizer",
  # "--disable-gpu-sandbox",
  # "--disable-accelerated-2d-canvas",
  # "--disable-accelerated-jpeg-decoding",
  # "--disable-accelerated-mjpeg-decode",
  # "--disable-accelerated-video-decode",
  # "--disable-accelerated-video-encode",
  # "--disable-backgrounding-occluded-windows",
  # "--disable-breakpad",
  # "--disable-component-extensions-with-background-pages",
  # "--disable-features=TranslateUI",
  # "--disable-features=Translate",
  # "--disable-features=NetworkService",
  return WebDriverConfig.DEFAULT_OPTIONS

def main() -> int:
  load_dotenv()
  try:
    parser = argparse.ArgumentParser(description="OTR Bot for ÖGF")
    parser.add_argument('-s', '--status', type=str, required=True, help="A betöltés státusza [Benyújtás, Döntés, Szerződés, Lezárás]") 
    parser.add_argument('-f', '--file', type=str, required=True, help="A betöltő fájl (*.xlsx)")
    parser.add_argument('-sp', '--supporter', type=str, required=True, help="Támogató [BM, KTM]")
    parser.add_argument('-b', '--begin', type=int, required=False, help="Kezdő sor (4)")
    parser.add_argument('-e', '--end', type=int, required=False, help="Vég sor (0)")
    
    args = parser.parse_args()

    if not validate_arguments(args):
      return 1

    config = Config.from_env()
    
    status_dict = {
      "Benyújtás": (1, "Start submission"),
      "Döntés": (2, "Start decision"),
      "Szerződés": (3, "Start contract"),
      "Lezárás": (4, "Start closing")
    }

    if args.status not in status_dict:
      logging.logger.error(f"Invalid status: {args.status}")
      return 1
    round_num, log_message = status_dict[args.status]
    logging.logger.info(log_message)

    runner = ModuleRunner(supporter=args.supporter)
    success = runner.load_datas(excel_file_path=args.file, sheet_name='betolt') \
      .start_driver(options=get_driver_options(), system=config.system, headless=False) \
      .login_otr(url=config.url, username=config.username, password=config.password) \
      .run(round=round_num)
    
    return 0 if success else 1
  except Exception as e:
    logging.logger.error(f"Unexpected error: {e}")
    return 1

if __name__ == "__main__": 
  sys.exit(main())