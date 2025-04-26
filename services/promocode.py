from services.dexid_client import DexidClient

def check_promocode(promocode):
    request_data, status_code = DexidClient.promocode_detail(promocode)
    if status_code != 200:
        return None
    return request_data