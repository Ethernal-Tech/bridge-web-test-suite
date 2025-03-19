import json
import requests
from sys import argv
from os import getenv
from time import sleep
from typing import Tuple
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor


class CardanoFaucet:
    def __init__(
            self,
            receive_addresses: list[str]
    ):

        self.__receive_addresses = receive_addresses

    @staticmethod
    def __mask(value: str) -> str:
        return "*" * 10 + value[-5:]

    def __get_fund_status(self, receive_address, response) -> Tuple[str, float]:
        tmp = f"{datetime.now()} Address: {self.__mask(receive_address)} "

        try:
            tmp += f"Error: {response['error']['tag']} {response['error']['contents'][0]}"
            return tmp, response['error']['contents'][0]
        except KeyError:
            tmp += "Success"
            return tmp, 0.0

    def __faucet_request(self, request_params, receive_address) -> str:
        status, tries = "", 2

        while tries > 0:
            response = requests.post(**request_params).json()
            status, ratelimit = self.__get_fund_status(receive_address, response)

            if ratelimit < 3600:
                sleep(ratelimit + 30)

            tries = 0 if ratelimit == 0 else tries - 1

        return status

    @staticmethod
    def __get_request_params(faucet_url, receive_address, api_key) -> dict:
        request_params = {
            "url": urljoin(faucet_url, receive_address),
            "params": {
                "api_key": api_key
            }
        }

        if getenv('BRD_PROXY_USERNAME') != '' and getenv('BRD_PROXY_PASSWORD') != '':
            request_params["proxies"] = {
                'http': f"http://{getenv('BRD_PROXY_USERNAME')}:{getenv('BRD_PROXY_PASSWORD')}@brd.superproxy.io:33335",
                'https': f"http://{getenv('BRD_PROXY_USERNAME')}:{getenv('BRD_PROXY_PASSWORD')}@brd.superproxy.io:33335"
            }

        return request_params

    def __preprod_faucet(self, receive_address) -> None:
        request_params = self.__get_request_params(
            faucet_url="https://faucet.preprod.world.dev.cardano.org/send-money/",
            receive_address=receive_address,
            api_key=getenv('PREPROD_FAUCET_API_KEY')
        )

        print(self.__faucet_request(request_params, receive_address))

    def __preview_faucet(self, receive_address) -> None:
        request_params = self.__get_request_params(
            faucet_url="https://faucet.preview.world.dev.cardano.org/send-money/",
            receive_address=receive_address,
            api_key=getenv('PREVIEW_FAUCET_API_KEY')
        )

        print(self.__faucet_request(request_params, receive_address))

    def fund(self, chain: str = "preview-testnet") -> None:
        with ThreadPoolExecutor(max_workers=15, thread_name_prefix="cardano-faucet") as pool:
            if chain == "preview-testnet":
                pool.map(self.__preview_faucet, self.__receive_addresses)
            elif chain == "preprod-testnet":
                pool.map(self.__preprod_faucet, self.__receive_addresses)
            else:
                print(f"{datetime.now()} Not supported chain")


if __name__ == '__main__':
    cardano_faucet = CardanoFaucet(receive_addresses=list(json.loads(getenv('CARDANO_TESTNET_WALLETS'))))
    cardano_faucet.fund(chain=argv[1].lower())
