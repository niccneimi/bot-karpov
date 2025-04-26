from asyncio.log import logger
import json
import os
import requests

from config import CRYPTOAPINET_API_KEY
from cryptoapinet.const import API_SERVICES, API_URLS, CRYPTOAPINET_VERSION


def add_param(param, value):
    if value is not None:
        return "&%s=%s" % (param, value)
    else:
        return ""


class CryptoapinetClient:
    def __init__(self, standart: str) -> None:
        self.standart = standart
        self.api_url = API_URLS[standart]
        if CRYPTOAPINET_VERSION == 1:
            self.api_key = getattr('', f"{API_SERVICES[standart].upper()}_API_KEY")
        else:
            self.api_key = CRYPTOAPINET_API_KEY
        

    def make_url(self, method, **kwargs):
        url = f"{self.api_url}{method}?key={self.api_key}"
        print("URL", url)
        for key in kwargs:
            if kwargs[key] is not None:
                url += add_param(key, kwargs[key])
        self.url = url
        print("URL", url)
        return url

    def give(self, **kwargs):
        """
        *tag - метка для IPN
        *uniqID - метка для адреса
        *address - адрес для сбора поступивших средств
        *token - ID токена
        *statusURL - ссылка IPN
        """
        method = "/bsc/.give"
        self.make_url(method, **kwargs)
        return self.process()

    def send(self, **kwargs):
        """
        *from
        address
        *token - ID токена
        amount
        memo
        *price
        *limit
        *statusURL
        *tag
        *uniqID
        *returnTransaction=1 - подождать и вернуть результат отправки
        """
        method = "/bnb/.send"
        self.make_url(method, **kwargs)
        return self.process()

    def process(self):
        response = requests.get(self.url)
        logger.info(
            "Process TronApiRequest",
            extra={
                "event": "ProcessTronApiRequest",
                # "url": self.url,
                "response": response.text,
            },
        )

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))
        else:
            return {
                "error": response.text,
                "status_code": response.status_code,
            }