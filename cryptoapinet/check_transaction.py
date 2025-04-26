from datetime import datetime, timedelta
import os
import requests

from config import BSCSCAN_API_KEY


def request_transaction_info(address: str):
    """
    Transaction info request at bscscan API
    """

    params = {
        'module': 'account',
        'action': 'tokentx',
        'address': address,
        'page': 1,
        'offset': 100,
        'startblock': 0,
        'endblock': 999999999,
        'sort': 'asc',
        'apikey': BSCSCAN_API_KEY
    }
    url = "https://api.bscscan.com/api"
    try:
        response = requests.get(url, params=params)
        tx_info = response.json()
        print(f'qwe - {tx_info}')
        if tx_info['status'] == "0":
            return 0, None
        
        current_time = datetime.now()
        time_threshold = current_time - timedelta(minutes=3000000)
        transaction = tx_info['result'][-1]
        transaction_time = datetime.fromtimestamp(int(transaction["timeStamp"]))
        if transaction_time >= time_threshold:
            confirmations = transaction['confirmations']
            return int(confirmations), transaction
    except Exception as err:
        print(f"Error: {err}")
        return None

print(request_transaction_info("0xaaaa1df1ca2a488ba15ff67b2e937f9759f478e2"))