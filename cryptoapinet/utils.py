from typing import Optional


def get_currency_cryptoapinet_by_token(token: Optional[str]):
    if token == "USDT" or token == "BSC-USD":
        return "USDT"
    if token:
        return token