from io import BytesIO

from cryptoapinet.const import BLOCKCHAIN_STANDART
from .client import CryptoapinetClient

import qrcode
from io import BytesIO

def get_payment_address(
    address_id, token=None, standart=BLOCKCHAIN_STANDART.BEP20
):

    client = CryptoapinetClient(standart=standart)
    response = client.give(token=token, uniqID=address_id)
    address = response["result"]["address"]
    print(address)
    return address


def get_qr_code_image(address: str) -> BytesIO:
    """
    Генерация QR-кода в формате PNG для указанного адреса.
    Возвращает объект BytesIO, содержащий изображение QR-кода.
    """
    qr_link = f"{address}"
    
    qr_code = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr_code.add_data(qr_link)
    qr_code.make(fit=True)

    img = qr_code.make_image(fill='black', back_color='white')
    
    virtual_file = BytesIO()
    img.save(virtual_file, format='PNG')
    virtual_file.seek(0)

    return virtual_file