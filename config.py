import os, yaml
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DEXID_USERNAME = os.getenv("DEXID_USERNAME")
DEXID_PASSWORD = os.getenv("DEXID_PASSWORD")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
CRYPTOAPINET_API_KEY = os.getenv("CRYPTOAPINET_API_KEY")
WALLET_ADDRESS = "0xaaaa1df1ca2a488ba15ff67b2e937f9759f478e2"

DATABASE_HOST = "91.84.111.102"
DATABASE_NAME = "vpnbotdatabase"
DATABASE_USERNAME = "niccneimivpn"
DATABASE_PASSWORD = "securepassword"

CLIENT_CONFIG_PATH = "/home/niccneimi/Documents/FREELANCE/vpnbotlord_karpov13/bot/client_config_template.json"

LANG_FILE = 'bot/lang.yml'

with open(LANG_FILE, 'r', encoding='utf-8') as f:
    LANG = yaml.safe_load(f)

NAME_VPN_CONFIG = 'DexPNBot'
COUNT_DAYS_TRIAL = 7
NICK_HELP = 'DexPN_Support_bot'
MANAGER_SERVER_HOST = '91.84.111.102'
MANAGER_SERVER_PORT = '8081'

def get_price_to_days(tarifs, price):
    PRICE_TO_DAYS_DICT = {tarif['price']: tarif['day'] for tarif in tarifs}
    return PRICE_TO_DAYS_DICT[price]