from os import path
from json import dump
from time import sleep
from typing import Union
from datetime import datetime
from toolbox.chrome import Chrome
from toolbox.utils import retry, find_element_by_xpath
from wallets.eternl import Eternl
from wallets.metamask import MetaMask


class ApexFusionReactor:
    def __init__(
            self,
            driver: Chrome,
            reactor_url: str,
            faucet_url: str,
            source_wallet: Union[Eternl, MetaMask],
            destination_wallet: Union[Eternl, MetaMask]
    ) -> None:

        self.__reactor_url: str = reactor_url
        self.__faucet_url: str = faucet_url
        self.__transactions_url: str = path.join(self.__reactor_url, 'transactions')
        self.__driver: Chrome = driver
        self.__source_wallet:  Union[Eternl, MetaMask] = source_wallet
        self.__destination_wallet: Union[Eternl, MetaMask] = destination_wallet
        self.__status_done: str = 'M10.1042 16.9856L5.47772 12.3802L7.02501 10.8123L10.1042 13.8964L17.0119 ' \
                                  '7.00977L18.559 8.55185L10.1042 16.9856Z'
        self.__final_status: str = 'Unknown'

        if datetime.today().strftime('%A') == 'Monday':
            self.__fund(self.__source_wallet.get_receive_address())
            self.__fund(self.__destination_wallet.get_receive_address())

    @retry()
    def __fund(self, receiver_address: str) -> None:
        self.__driver.get(self.__faucet_url)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="address"]'
        ).send_keys(receiver_address)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="app"]/div/div[2]/main/div/div[2]/div/div/form/div[2]/button'
        ).click()

        print(f'{datetime.now()} Receiver Address {receiver_address} has been funded')

    @retry()
    def __open_reactor(self, source: str, destination: str) -> None:
        self.__driver.get(self.__reactor_url)

        sleep(5)

        self.__driver.execute_script(f"window.localStorage.setItem('selected_chain', '{source}');")
        self.__driver.execute_script(f"window.localStorage.setItem('destination_chain', '{destination}');")

        sleep(5)

        self.__driver.refresh()

    @retry()
    def __connect_wallet_and_move_funds(self) -> None:
        # wait for the button to be available
        sleep(10)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="root"]/div[1]/div[2]/div/button'
        ).click()

    @retry()
    def __disconnect_wallet(self):
        find_element_by_xpath(
            self.__driver,
            '//*[@id="basic-button"]',
        ).click()

        sleep(1)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="basic-menu"]/div[3]/ul/li'
        ).click()

    @retry()
    def __destination_address(self, destination_address: str) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[2]/div/div/input'
        ).send_keys(destination_address)

    @retry()
    def __amount_to_send(self, amount: str) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id=":rb:"]'
        ).send_keys(amount)

    @retry()
    def __set_balance(self) -> None:
        balance = find_element_by_xpath(
            self.__driver,
            '//*[@id="root"]/div[1]/div[2]/div/div/div[3]/div[1]/p'
        ).text

        self.__balance = float(balance)

    @retry()
    def __send_tx(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[3]/button[2]'
        ).click()

    @retry()
    def __open_popup_for_signing_tx(self) -> None:
        tries = 12
        tabs = self.__driver.window_handles

        while tries > 0 and self.__driver.window_handles == tabs:
            tries -= 1
            sleep(5)

        self.__driver.switch_to.window(list(set(self.__driver.window_handles) - set(tabs))[0])

    @retry()
    def __sign_transaction(self, password: str) -> None:
        find_element_by_xpath(
            self.__driver, '//*[@id="password"]'
        ).send_keys(password)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="GridFormSignWithPassword"]/button[3]'
        ).click()

        # wait for the transaction to be signed
        sleep(15)

        self.__driver.switch_to.window(self.__driver.get_init_tab())

    @retry()
    def __confirm_transaction(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="app-content"]/div/div/div/div/div[3]/button[2]'
        ).click()

        # wait for the transaction to be confirmed
        sleep(5)

        self.__driver.switch_to.window(self.__driver.get_init_tab())

    @retry()
    def __progress(self, xpath: str) -> bool:
        sleep(10)

        tries = 200

        while tries > 0:
            status = find_element_by_xpath(
                self.__driver,
                xpath
            ).get_attribute('d')

            if status == self.__status_done:
                return True

            else:
                tries -= 1
                sleep(3)

        return False

    def __progress_source(self) -> bool:
        return self.__progress('//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[1]/div[1]/div/div[2]'
                               '//*[local-name()="svg"]//*[local-name()="path"]')

    def __progress_bridge(self) -> bool:
        return self.__progress('//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[1]/div[2]/div/div[2]'
                               '//*[local-name()="svg"]//*[local-name()="path"]')

    def __progress_destination(self) -> bool:
        return self.__progress('//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[1]/div[3]/div/div[2]'
                               '//*[local-name()="svg"]//*[local-name()="path"]')

    @retry()
    def __get_status(self) -> str:
        self.__driver.get(self.__transactions_url)

        # wait the bridging history to be loaded
        sleep(15)

        # filter by Destination
        find_element_by_xpath(
            self.__driver,
            '//*[@id="root"]/div[1]/div[2]/div/div[1]/div/div/button'
        ).click()

        sleep(1)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="destination-chain"]'
        ).click()

        sleep(1)

        find_element_by_xpath(
            self.__driver,
            f'//*[starts-with(@id, ":r")]//*[contains(text(), "{self.__destination_wallet.get_name().capitalize()}")]'
        ).click()

        sleep(1)

        find_element_by_xpath(
            self.__driver,
            '/html/body/div[2]/div[3]/div[2]/button[2]'
        ).click()

        # wait the bridging history to be loaded
        sleep(15)

        status = find_element_by_xpath(
            self.__driver,
            '//*[@id="root"]/div[1]/div[2]/div/div[2]/table/tbody/tr[1]/td[7]/div/p'
        ).text

        if status != 'Success':
            sleep(10)

            # try again
            raise Exception

        return status

    @staticmethod
    def __not_possible_bridging(source: str, destination: str) -> None:
        print(f"{datetime.now()} Error: For source '{source}' destination can't be '{destination}'")

    def bridging(self, amount: str) -> None:
        self.__source_wallet.toggle()

        self.__open_reactor(self.__source_wallet.get_name(), self.__destination_wallet.get_name())

        self.__connect_wallet_and_move_funds()

        print(f'{datetime.now()} {type(self.__source_wallet).__name__} Wallet is waiting for access to {self.__reactor_url} to be granted')
        self.__source_wallet.grant_access()
        print(f'{datetime.now()} Access granted successfully')

        self.__connect_wallet_and_move_funds()

        self.__destination_address(self.__destination_wallet.get_receive_address())
        self.__amount_to_send(amount)
        self.__set_balance()
        self.__send_tx()

        self.__open_popup_for_signing_tx()

        if type(self.__source_wallet) == Eternl:
            self.__sign_transaction(self.__source_wallet.get_sign_key())

        elif type(self.__source_wallet) == MetaMask:
            self.__confirm_transaction()

        print(f"{datetime.now()} Starting bridging from '{self.__source_wallet.get_name()}' to "
              f"'{self.__destination_wallet.get_name()}' {amount} token(s)")

        is_source_succeeded: bool = self.__progress_source()
        print(f'{datetime.now()} Source succeeded: {is_source_succeeded}')

        is_bridge_succeeded: bool = self.__progress_bridge()
        print(f'{datetime.now()} Bridge succeeded: {is_bridge_succeeded}')

        is_destination_succeeded: bool = self.__progress_destination()
        print(f'{datetime.now()} Destination succeeded: {is_destination_succeeded}')

        try:
            self.__final_status = self.__get_status()
        except Exception:
            pass
        finally:
            print(f'{datetime.now()} Bridging status: {self.__final_status}')

        try:
            self.__disconnect_wallet()
            self.__source_wallet.toggle()
        except Exception:
            # If this fails, it won't make a difference anyway
            pass

        dump(
            obj={
                'status': self.__final_status.lower(),
                'source': is_source_succeeded,
                'bridge': is_bridge_succeeded,
                'destination': is_destination_succeeded
            },
            fp=open(
                file=f'/tmp/{self.__source_wallet.get_name()}_to_{self.__destination_wallet.get_name()}.json',
                mode='w',
                encoding='utf-8'
            ),
            indent=4
        )
