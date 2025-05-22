import os, yaml
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DEXID_USERNAME = os.getenv("DEXID_USERNAME")
DEXID_PASSWORD = os.getenv("DEXID_PASSWORD")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
CRYPTOAPINET_API_KEY = os.getenv("CRYPTOAPINET_API_KEY")
WALLET_ADDRESS = "0xaaaa1df1ca2a488ba15ff67b2e937f9759f478e2"

ADMIN_DXNP_USERNAME = os.getenv("ADMIN_DXNP_USERNAME")
ADMIN_DXNP_PASSWORD = os.getenv("ADMIN_DXNP_PASSWORD")

DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

CLIENT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'client_config_template.json')

LANG_FILE = os.path.join(os.path.dirname(__file__), 'lang.yml')

with open(LANG_FILE, 'r', encoding='utf-8') as f:
    LANG = yaml.safe_load(f)

NAME_VPN_CONFIG = 'DexPNBot'
COUNT_DAYS_TRIAL = 7
NICK_HELP = 'DexPN_Support_bot'
MANAGER_SERVER_HOST = os.getenv("MANAGER_SERVER_HOST")
MANAGER_SERVER_PORT = os.getenv("MANAGER_SERVER_PORT")

def get_price_to_days(tarifs, price):
    PRICE_TO_DAYS_DICT = {tarif['price']: tarif['day'] for tarif in tarifs}
    return PRICE_TO_DAYS_DICT[price]