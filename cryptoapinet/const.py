class DictContainer:
    def __init__(self, **main_dict):
        self.__dict__.update(main_dict)

    def items(self):
        return self.__dict__.items()
    
    def __getitem__(self, key):
        return self.__dict__[key]


CURRENCIES = DictContainer(
    USDT="USDT",
    DEXNET="DEXNET (-20%)"
)


BLOCKCHAIN_STANDART = DictContainer(
    BEP20="BEP20",
    DEFAULT="BEP20"
)


API_URLS = DictContainer(
    BEP20="https://new.cryptocurrencyapi.net/api",
)


API_SERVICES = DictContainer(
    BEP20="bnbapinet"
)


CRYPTOAPINET_VERSION = 2