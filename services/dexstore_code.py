import requests
from decimal import Decimal
from requests.auth import HTTPBasicAuth
from config import ADMIN_DXNP_USERNAME, ADMIN_DXNP_PASSWORD


API_VERSION = "v1"
API_URL = f"https://admin.dpntg.online/api/{API_VERSION}"

#ОТПРАВКА ЗАПРОСОВ НА СТОРОНУ АДМИНКИ, ГДЕ ХРАНЯТСЯ ПРОМОКОДЫ
#TODO ЖЕЛАТЕЛЬНО СДЕЛАТЬ ОТПРАВУ АССИНХРОННОЙ, ПО ВОЗМОЖНОСТИ. requests НЕ ПОДДЕРЖЖИВАЕТ
class AdminDPNClient:

    @classmethod
    def _process_request(cls, url, method, payload):
        auth = HTTPBasicAuth(ADMIN_DXNP_USERNAME, ADMIN_DXNP_PASSWORD)
        if method == "GET":
            response = requests.get(url, params=payload, auth=auth)
        elif method in ["POST", "PUT"]:
            response = requests.request(method, url, json=payload, auth=auth)
        return response.json(), response.status_code
        
    @classmethod
    def check_code(cls, request_data):
        url = f"{API_URL}/promotions/check-code/"
        payload = request_data
        data = cls._process_request(url, "POST", payload=payload)
        return data
    
    @classmethod
    def activate_code(cls, request_data):
        url = f"{API_URL}/promotions/activate-code/"
        payload = request_data
        data = cls._process_request(url, "POST", payload=payload)
        return data 