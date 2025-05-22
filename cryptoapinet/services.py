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
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = BytesIO()
    img.save(img_io)

    return img_io