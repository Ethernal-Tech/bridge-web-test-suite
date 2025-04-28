from os import path
from json import dump
from time import sleep
from typing import Union
from datetime import datetime
from toolbox.chrome import Chrome
from wallets.eternl import Eternl
from wallets.metamask import MetaMask
from toolbox.utils import Network, retry
from toolbox.utils import ApexFusionSubnetwork, CardanoSubnetwork


class Bridge:
    def __init__(
            self,
            driver: Chrome,
            bridge_name: str,
            bridge_url: str,
            apex_faucet_url: str,
            source_wallet: Union[Eternl, MetaMask],
            destination_wallet: Union[Eternl, MetaMask]
    ) -> None:

        self.__bridge_name: str = bridge_name
        self.__bridge_url: str = path.join(bridge_url, 'dashboard') if self.__bridge_name == 'skyline' else bridge_url
        self.__apex_faucet_url: str = apex_faucet_url
        self.__transactions_url: str = path.join(bridge_url, 'transactions')
        self.__driver: Chrome = driver
        self.__source_wallet: Union[Eternl, MetaMask] = source_wallet
        self.__destination_wallet: Union[Eternl, MetaMask] = destination_wallet
        self.__status_done: str = 'M10.1042 16.9856L5.47772 12.3802L7.02501 10.8123L10.1042 13.8964L17.0119 ' \
                                  '7.00977L18.559 8.55185L10.1042 16.9856Z'
        self.__transaction_signed_error: str = ""
        self.__is_source_succeeded: bool = False
        self.__is_bridge_succeeded: bool = False
        self.__is_destination_succeeded: bool = False
        self.__final_status: str = 'Unknown'

        # TODO: Add support for Cardano Preview Faucet
        if datetime.today().strftime('%A') == 'Monday' and \
                self.__source_wallet.get_subnetwork() != CardanoSubnetwork.preview:

            self.__fund(self.__source_wallet.get_receive_address())

    @retry()
    def __fund(self, receiver_address: str) -> None:
        print(f'{datetime.now()} Get funds from {self.__apex_faucet_url}')

        self.__driver.get(self.__apex_faucet_url)

        self.__driver.find_element_by_xpath(
            '//*[@id="address"]'
        ).send_keys(receiver_address)

        self.__driver.find_element_by_xpath(
            '//*[@id="app"]/div/div/div[2]/main/div/div[2]/div/div/form/div[2]/button'
        ).click()

        print(f'{datetime.now()} {receiver_address} has been funded')

    @retry()
    def __open_bridge_app(self, source: str, destination: str) -> None:
        self.__driver.get(self.__bridge_url)

        sleep(5)

        self.__driver.execute_script(f"window.localStorage.setItem('selected_chain', '{source}');")
        self.__driver.execute_script(f"window.localStorage.setItem('destination_chain', '{destination}');")

        sleep(5)

        self.__driver.refresh()

    @retry()
    def __connect_wallet_and_move_funds(self) -> None:
        # wait for the button to be available
        sleep(10)

        self.__driver.find_element_by_xpath(
            '//*[@id="root"]/div[1]/div[2]/div/button'
        ).click()

    @retry()
    def __destination_address(self, destination_address: str) -> None:
        self.__driver.find_element_by_xpath(
            '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[2]/div/div/input'
        ).send_keys(destination_address)

    def __select_token(self) -> None:
        if self.__bridge_name == 'skyline':

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[3]/div'
            ).click()

            sleep(1)

            self.__driver.find_element_by_xpath(
                f'//*[starts-with(@id, "menu")]'
                f'//*[translate(text(), '
                f'"ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
                f'"abcdefghijklmnopqrstuvwxyz") = '
                f'"{self.__source_wallet.get_token_name()}"]'
            ).click()

            sleep(1)

    @retry()
    def __amount_to_send(self, amount: str) -> None:
        if self.__source_wallet.get_web_app_identifier() != Network.cardano and \
                self.__destination_wallet.get_web_app_identifier() != Network.cardano:

            self.__driver.find_element_by_xpath(
                '//*[@id=":rb:"]'
            ).send_keys(amount)

        else:

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[4]/div[1]/div/div/div/input'
            ).send_keys(amount)

    @retry()
    def __send_tx(self) -> None:
        # Scroll to the bottom of the page
        self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait 15sec before submit transaction
        sleep(15)

        if self.__bridge_name == 'reactor':

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[3]/button[2]'
            ).click()

        elif self.__bridge_name == 'skyline':

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[4]/button[2]'
            ).click()

        else:
            raise Exception

    @retry()
    def __open_popup_for_signing_tx(self) -> None:
        tries = 12
        tabs = self.__driver.window_handles

        while tries > 0 and self.__driver.window_handles == tabs:
            tries -= 1
            sleep(5)

        self.__driver.switch_to.window(list(set(self.__driver.window_handles) - set(tabs))[0])

    @retry()
    def __sign_transaction(self, password: str) -> str:
        self.__driver.find_element_by_xpath(
            '//*[@id="passwordInput"]'
        ).send_keys(password)

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-sign-tx"]/div/div/div/div[2]/div[2]/div/div/div/div[4]/div[2]/button[2]'
        ).click()

        # wait for the transaction to be signed
        sleep(15)

        # check if the transaction successfully signed
        try:

            error = self.__driver.find_element_by_xpath(
                '//*[@id="eternl-sign"]/div/div/div/div[2]/div[2]/div/div[5]/div[2]/div'
            ).text

            print(f"{datetime.now()} Sign transaction error: {error}")

            return error

        except Exception:

            print(f"{datetime.now()} Transaction successfully signed")
            pass

        self.__driver.switch_to.window(self.__driver.get_init_tab())

        return ""

    @retry()
    def __confirm_transaction(self) -> None:
        self.__driver.find_element_by_xpath(
            '//*[@id="app-content"]/div/div/div/div/div[3]/button[2]'
        ).click()

        # wait for the transaction to be confirmed
        sleep(5)

        self.__driver.switch_to.window(self.__driver.get_init_tab())

    def __progress(self, xpath: str, timeout: int = 600) -> bool:
        sleep(10)

        tries = int(timeout / 3)

        while tries > 0:
            try:

                status = self.__driver.find_element_by_xpath(xpath).get_attribute('d')

                if status == self.__status_done:
                    return True

            except Exception:
                pass

            tries -= 1
            sleep(3)

        return False

    def __progress_source(self) -> bool:
        if self.__bridge_name == 'skyline':
            timeout = 1800
        else:
            timeout = 600

        return self.__progress(
            '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[1]/div[1]/div/div[2]'
            '//*[local-name()="svg"]//*[local-name()="path"]',
            timeout
        )

    def __progress_bridge(self) -> bool:
        if self.__bridge_name == 'skyline' or self.__destination_wallet.get_subnetwork() == ApexFusionSubnetwork.prime:
            timeout = 1800
        else:
            timeout = 600

        return self.__progress(
            '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[1]/div[2]/div/div[2]'
            '//*[local-name()="svg"]//*[local-name()="path"]',
            timeout)

    def __progress_destination(self) -> bool:
        if self.__bridge_name == 'skyline':
            timeout = 1800
        else:
            timeout = 600

        return self.__progress(
            '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[1]/div[3]/div/div[2]'
            '//*[local-name()="svg"]//*[local-name()="path"]',
            timeout
        )

    @retry()
    def __get_status(self) -> str:
        self.__driver.get(self.__transactions_url)

        # wait the bridging history to be loaded
        sleep(30)

        # filter by Destination
        self.__driver.find_element_by_xpath(
            '//*[@id="root"]/div[1]/div[2]/div/div[1]/div/div/button'
        ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="destination-chain"]'
        ).click()

        sleep(3)

        self.__driver.find_element_by_xpath(
            f'//*[starts-with(@id, ":r")]'
            f'//*[translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
            f'"abcdefghijklmnopqrstuvwxyz") = '
            f'"{self.__destination_wallet.get_web_app_identifier()}"]'
        ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '/html/body/div[2]/div[3]/div[2]/button[2]'
        ).click()

        # wait the bridging history to be loaded
        sleep(30)

        if self.__bridge_name == 'reactor':

            status = self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/table/tbody/tr[1]/td[7]/div/p'
            ).text

        elif self.__bridge_name == 'skyline':

            status = self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/table/tbody/tr[1]/td[8]/div/p'
            ).text

        else:
            raise Exception

        if status != 'Success':
            sleep(10)

            # try again
            raise Exception

        return status

    def bridging(self, amount: str) -> str:
        self.__source_wallet.toggle()

        self.__open_bridge_app(
            self.__source_wallet.get_web_app_identifier(),
            self.__destination_wallet.get_web_app_identifier()
        )

        self.__connect_wallet_and_move_funds()

        print(f'{datetime.now()} Waiting for access to {self.__bridge_url} to be granted')
        self.__source_wallet.grant_access()
        print(f'{datetime.now()} Access granted successfully')

        self.__connect_wallet_and_move_funds()

        self.__destination_address(self.__destination_wallet.get_receive_address())
        self.__select_token()
        self.__amount_to_send(amount)
        self.__send_tx()
        
        self.__open_popup_for_signing_tx()
        
        if type(self.__source_wallet) == Eternl:
            self.__transaction_signed_error = self.__sign_transaction(self.__source_wallet.get_sign_key())
        
        elif type(self.__source_wallet) == MetaMask:
            self.__confirm_transaction()
        
        if self.__transaction_signed_error != "":
            dump(
                obj={
                    'status': 'failed',
                    'source': False,
                    'bridge': False,
                    'destination': False
                },
                fp=open(
                    file=f'/tmp/statuses.json',
                    mode='w',
                    encoding='utf-8'
                ),
                indent=4
            )

            return self.__transaction_signed_error

        print(f"{datetime.now()} Start bridging")

        try:

            self.__is_source_succeeded = self.__progress_source()
            print(f'{datetime.now()} Source succeeded: {self.__is_source_succeeded}')
            
            self.__is_bridge_succeeded = self.__progress_bridge()
            print(f'{datetime.now()} Bridge succeeded: {self.__is_bridge_succeeded}')
            
            self.__is_destination_succeeded: bool = self.__progress_destination()
            print(f'{datetime.now()} Destination succeeded: {self.__is_destination_succeeded}')

            self.__final_status = self.__get_status()
            print(f'{datetime.now()} Bridging status: {self.__final_status}')

        except Exception:
            # the progress status may occasionally fail to be detected,
            # but the implementation makes refreshing the page to retry checking the status impossible
            pass

        dump(
            obj={
                'status': self.__final_status.lower(),
                'source': self.__is_source_succeeded,
                'bridge': self.__is_bridge_succeeded,
                'destination': self.__is_destination_succeeded
            },
            fp=open(
                file=f'/tmp/statuses.json',
                mode='w',
                encoding='utf-8'
            ),
            indent=4
        )

        return ""
