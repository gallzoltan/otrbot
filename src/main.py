import os
import argparse
import otrbot.otr_logging as logging
from dotenv import load_dotenv
from otrbot.runner import ModuleRunner

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
  return (            
    "--no-sandbox",
    "--disable-extensions"    
  )

def get_env_vars(env):
  if env == "dev":
    return os.getenv('SYSTEM'), os.getenv("OTR_EDU_URL"), os.getenv("OTR_EDU_USERNAME"), os.getenv("OTR_EDU_PASSWORD")
  else:
    return os.getenv('SYSTEM'), os.getenv("OTR_URL"), os.getenv("OTR_USERNAME"), os.getenv("OTR_PASSWORD")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--status', type=str, required=True, help="A betöltés státusza [Benyújtás, Döntés, Szerződés, Lezárás]") 
  parser.add_argument('-f', '--file', type=str, required=True, help="A betöltő fájl (*.xlsx)")
  parser.add_argument('-sp', '--supporter', type=str, required=True, help="Támogató [BM, KTM]")
  parser.add_argument('-b', '--begin', type=int, required=False, help="Kezdő sor (4)")
  parser.add_argument('-e', '--end', type=int, required=False, help="Vég sor (0)")
  
  args = parser.parse_args()

  logging.logger.info(f"Start script with: {args.status} status and {args.file} file")
  load_dotenv()
  system, url, username, password = get_env_vars(os.getenv("ENV"))
  
  status_dict = {
    "Benyújtás": (1, "Start submission"),
    "Döntés": (2, "Start decision"),
    "Szerződés": (3, "Start contract"),
    "Lezárás": (4, "Start closing")
  }
  
  if args.status in status_dict:
    round, log_message = status_dict[args.status]
    logging.logger.info(log_message)
  else:
    logging.logger.error(f"Invalid status: {args.status}")
    return

  runner = ModuleRunner(supporter=args.supporter)
  runner.load_datas(excel_file_path=args.file, sheet_name='betolt') \
    .start_driver(options=get_driver_options(), system=system, headless=False) \
    .login_otr(url=url, username=username, password=password) \
    .run(round=round)

if __name__ == "__main__": 
  main()