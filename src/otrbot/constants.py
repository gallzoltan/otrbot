from enum import Enum


class Navigate(Enum):
  MENU_TAMOGATASOK = "//div[@id='menu_tamogatasok']/div"
  MENU_TAMOGATASOK2 = "https://edu.otr.gov.hu/app/tamogatasok_menu"
  MENU_LIST_TAMOGATAS = "//*[@id='menu_tamogatasok_kereses']" 
  MENU_UJ_TAMOGATAS = "//div[@id='menu_uj_tamogatas_igeny']/div"
  TAB_MAIN_CLAIMING = "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/ul/li/a/tab-heading"  
  TAB_SUB_CLAIMING = (
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/div/div/igenylo-tab/div/ul/li[1]/a/tab-heading", 
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/div/div/igenylo-tab/div/ul/li[2]/a/tab-heading"
  )
  TAB_MAIN_CLAIM = "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/ul/li[2]/a/tab-heading"
  TAB_SUB_CLAIM = (
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/div/div[2]/div/ul/li[1]/a/tab-heading",
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/div/div[2]/div/ul/li[2]/a/tab-heading",
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ng-form/div[3]/div/div[2]/div/ul/li[3]/a/tab-heading"
  )
  TAB_MAIN_DECISION = "//*[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/ul/li[4]/a/tab-heading"
  TAB_SUB_DECISION = (
    "//*[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[4]/div/ul/li[1]/a/tab-heading",
    "//*[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[4]/div/ul/li[2]/a/tab-heading",
    "//*[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[4]/div/ul/li[3]/a/tab-heading",
    "//*[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[4]/div/ul/li[4]/a/tab-heading"
  )
  TAB_MAIN_CONTRACT = "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/ul/li[5]/a/tab-heading"
  TAB_SUB_CONTRACT = (
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[5]/div/ul/li[1]/a/tab-heading",
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[5]/div/ul/li[2]/a/tab-heading",
    "//div[@id='otr_angular_inner']/div/div/div/div/div/div/ui-view/ng-form/div[3]/div/div[5]/div/ul/li[3]/a/tab-heading"
  )


class SubmitForms(Enum):
  ERROR_NOTICE = "//*[@id='otr_angular_inner']/div/div/div/div[1]/div/span[2]"
  BUTTON_VALIDATION = "//button[@id='tamogatasi_igeny_rogzitese:ellenorzes']"
  BUTTON_SAVE = "//button[@id='tamogatasi_igeny_rogzitese:mentes']"
  # BUTTON_FIX = "//button[@id='tamogatasi_igeny_rogzitese:RogzitesKesz']"
  BUTTON_FIX = "//button[@id='tamogatasi_igeny_rogzitese:{what}']"
  BUTTON_CLOSE = "//*[@id='tamogatasi_igeny_rogzitese:Lezaras']"
  BUTTON_KILEP = "//button[@id='tamogatasi_igeny_rogzitese:visszalepes']"
  BUTTON_VISSZALEP = "//*[@id='tamogatasi_igeny_rogzitese:Visszalepes']"

class Categories(Enum):
  ''' categories '''
  CAT_TITLES = {
    "4.": "4. Csekély összegű (de minimis) támogatás",
    "4.1.": "4.1. Általános csekély összegű (de minimis) támogatás (1407/2013/EU bizottsági rendelet)",
    "4.1.1.": "4.1.1. Általános csekély összegű (de minimis) támogatás nem közúti árufuvarozó részére",
    "9.": "9. Közszolgáltatásért nyújtott állami támogatás",
    "9.2.": "9.2. Az 1370/2007/EK európai parlamenti és tanácsi rendelet hatálya alá tartozó állami támogatás",
    "9.4.": "9.4. A 360/2012/EU bizottsági rendelet hatálya alá tartozó csekély összegű közszolgáltatási támogatás",
    "18.": "18. Nem állami támogatás"
  }