import requests
from requests.auth import HTTPBasicAuth
from config import DEXID_USERNAME, DEXID_PASSWORD


API_URL = "https://api.dexid.dexnet.one"


class DexidClient:

    @classmethod
    def _process_request(cls, url, method, payload):
        auth = HTTPBasicAuth(DEXID_USERNAME, DEXID_PASSWORD)
        if method == "GET":
            response = requests.get(url, params=payload, auth=auth)
        elif method in ["POST", "PUT"]:
            response = requests.request(method, url, json=payload, auth=auth)
        return response.json(), response.status_code
        
    @classmethod
    def send_callback(cls, request_data):
        url = f"{API_URL}/api/v1/companies/callback/register/"
        payload = request_data
        data = cls._process_request(url, "POST", payload=payload)
        return data
    
    @classmethod
    def validate_promocode(cls, code):
        url = f"{API_URL}/api/v1/accounts/promocode/validate/"
        payload = {
            "code": code
        }
        data = cls._process_request(url, "POST", payload=payload)
        return data
    
    @classmethod
    def promocode_detail(cls, code):
        url = f"{API_URL}/api/v1/accounts/promocode/detail/"
        payload = {
            "code": code
        }
        data = cls._process_request(url, "POST", payload=payload)
        return data