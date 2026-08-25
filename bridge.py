from json import dump
from time import sleep
from typing import Union
from os import getenv, path
from toolbox.chrome import Chrome
from toolbox.logger import logger
from wallets.eternl import Eternl
from wallets.metamask import MetaMask
from selenium.common.exceptions import NoSuchElementException
from toolbox.utils import ApexFusionSubnetwork, CardanoSubnetwork, retry


class Bridge:
    def __init__(
            self,
            driver: Chrome,
            bridge_name: str,
            bridge_url: str,
            source_wallet: Union[Eternl, MetaMask],
            destination_wallet: Union[Eternl, MetaMask]
    ) -> None:

        self.__bridge_name: str = bridge_name.capitalize()
        self.__bridge_url: str = path.join(bridge_url, "bridge-app") if self.__bridge_name == "Skyline" else bridge_url
        self.__driver: Chrome = driver
        self.__source_wallet: Union[Eternl, MetaMask] = source_wallet
        self.__destination_wallet: Union[Eternl, MetaMask] = destination_wallet
        self.__status_done: str = "M20 6 9 17l-5-5" if self.__bridge_name == "Skyline" else \
            "M10.1042 16.9856L5.47772 12.3802L7.02501 10.8123L10.1042 13.8964L17.0119 " \
            "7.00977L18.559 8.55185L10.1042 16.9856Z"
        self.__tx_id: str = "Unknown"
        self.__is_source_succeeded: bool = False
        self.__is_bridge_succeeded: bool = False
        self.__is_destination_succeeded: bool = False
        self.__final_status: str = "Unknown"

    @retry()
    def __sentry(self, accept: bool) -> None:

        if self.__bridge_name == "Skyline":

            logger.debug(f"Accepting sentry dialog: {accept}")

            self.__driver.find_element_by_xpath(
                f'/html/body/div[2]/div/div/button[{"1" if accept else "2"}]'
            ).click()

            sleep(3)

            logger.debug("Sentry dialog closed")

    @retry()
    def __open_bridge_app(self, source: str, destination: str) -> None:

        logger.debug(f"Opening {self.__bridge_name} Bridge on {self.__bridge_url}")

        self.__driver.get(self.__bridge_url)
        sleep(3)

        logger.debug(f"{self.__bridge_name} Bridge opened successfully")

        logger.debug(f"Setting the source chain to {source} and the destination chain to {destination}")

        self.__driver.execute_script(f"window.localStorage.setItem('selected_chain', '{source.lower()}');")
        self.__driver.execute_script(f"window.localStorage.setItem('destination_chain', '{destination.lower()}');")

        sleep(1)

        logger.debug("Source and destination chains set successfully")

        logger.debug(f"Reloading the {self.__bridge_name} Bridge")

        self.__driver.refresh()
        sleep(10)

        logger.debug(f"{self.__bridge_name} Bridge reloaded successfully")

    @retry(tries=5)
    def __connect_wallet(self) -> None:

        logger.debug(
            f"Connecting {self.__source_wallet.get_subnetwork()} wallet "
            f"to the {self.__bridge_name} Bridge"
        )

        # Scroll to the bottom of the page
        self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        self.__driver.find_element_by_xpath(
            '//*[@id="bridge-connect"]'
        ).click()

        sleep(3)

        logger.debug(f"{self.__source_wallet.get_subnetwork()} wallet connected successfully")

    @retry(tries=5)
    def __check_connected_wallet(self) -> bool:

        logger.debug(f"Checking if the {self.__source_wallet.get_subnetwork()} wallet is connected correctly")

        connected_wallet: str = self.__driver.find_element_by_xpath(
            '//*[@id="basic-button"]'
        ).text.lower()

        receive_address: str = self.__source_wallet.get_receive_address().lower()
        receive_address_short: str = f"{receive_address[:7]}...{receive_address[-5:]}"

        if connected_wallet != receive_address_short:

            logger.debug(
                f"{self.__source_wallet.get_subnetwork()} wallet is not connected correctly"
            )

            logger.debug(f"Connected wallet address: {connected_wallet}")
            logger.debug(f"Receive wallet address: {receive_address_short}")

            return False

        logger.debug(
            f"{self.__source_wallet.get_subnetwork()} wallet is connected correctly"
        )
        return True

    @retry(tries=5)
    def __disconnect_wallet(self) -> None:

        logger.debug(
            f"Disconnecting {self.__source_wallet.get_subnetwork()} wallet "
            f"from the {self.__bridge_name} Bridge"
        )

        self.__driver.find_element_by_xpath(
            '//*[@id="basic-button"]'
        ).click()

        sleep(1)

        if self.__bridge_name != "Skyline":

            self.__driver.find_element_by_xpath(
                '//*[@id="basic-menu"]/div[3]/ul/li'
            ).click()

        sleep(3)

        logger.debug(f"{self.__source_wallet.get_subnetwork()} wallet disconnected successfully")

    @retry(tries=5)
    def __move_funds(self) -> None:

        logger.debug(f"Moving funds to {self.__destination_wallet.get_subnetwork()}")

        # Scroll to the bottom of the page
        self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        self.__driver.find_element_by_xpath(
            '//*[@id="move-funds"]'
        ).click()

        sleep(1)

        logger.debug(f"{self.__destination_wallet.get_subnetwork()} ready to receive funds")

    @retry()
    def __destination_address(self, destination_address: str) -> None:

        logger.debug(f"Inserting destination address as {self.__destination_wallet.get_receive_address()}")

        self.__driver.find_element_by_xpath(
            '//*[@id="dest-addr"]'
        ).send_keys(destination_address)

        logger.debug("The Destination address inserted successfully")

        sleep(1)

    @retry()
    def __select_token(self) -> None:

        if self.__bridge_name == "Skyline":

            logger.debug(f"Search source token: {self.__source_wallet.get_token_name()}")

            self.__driver.find_element_by_xpath(
                '//*[@id="src-tokens"]'
            ).click()

            sleep(1)

            try:

                self.__driver.find_element_by_xpath(
                    '//*[@id="search-tokens"]'
                ).send_keys(self.__source_wallet.get_token_name().lower())

                sleep(1)

                self.__driver.find_element_by_xpath(
                    '/html/body/div[2]/div[2]/div[5]/div/ul/li[1]/button'
                ).click()

            except NoSuchElementException:
                pass

            logger.debug("Source token selected")

            logger.debug("Re-check selected source token")

            check_selected_token: str = self.__driver.find_element_by_xpath(
                '//*[@id="src-tokens"]/span[1]/span/span[1]'
            ).text.lower()

            if check_selected_token == self.__source_wallet.get_token_name().lower():

                logger.debug("Source token selected successfully")

            else:

                raise ValueError("Source token selected is not the expected one")

            sleep(1)

    @retry()
    def __amount_to_send(self, amount: str) -> None:

        logger.debug(f"Inserting {amount} tokens to be bridged")

        self.__driver.find_element_by_xpath(
            '//*[@id="bridge-amount"]'
        ).send_keys(amount)

        logger.debug("Amount of tokens inserted successfully")

        # wait to calculate fee
        sleep(15)

    @retry()
    def __send_tx(self) -> None:

        logger.debug(
            f"Confirming bridging from {self.__source_wallet.get_subnetwork()} to "
            f"{self.__destination_wallet.get_subnetwork()}"
        )

        # Scroll to the bottom of the page
        self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        self.__driver.find_element_by_xpath(
            '//*[@id="bridge-tx"]'
        ).click()

        sleep(5)

    @retry(tries=5)
    def __get_tx_id(self) -> str:

        logger.debug("Getting transaction ID")

        tx_id: str = self.__driver.find_element_by_xpath(
            '//link[@rel="canonical"]'
        ).get_attribute("href").rsplit("/", 1)[1]

        try:

            # check if tx_id is a number
            int(tx_id)

            logger.info(f"Transaction ID: {tx_id}")

            return tx_id

        except ValueError:

            logger.debug("Transaction ID not found")
            raise

    @retry()
    def __progress(self, xpath: str, tries: int) -> bool:

        logger.debug("Getting progress status every 1sec")

        while tries > 0:

            try:

                status = self.__driver.find_element_by_xpath(xpath).get_attribute("d")

                if status == self.__status_done:
                    logger.debug("Progress is done")
                    return True

            except NoSuchElementException:
                pass

            tries -= 1
            logger.debug(f"Progress is not done yet. Remaining progress status tries: {tries}")
            sleep(1)

        return False

    def __progress_source(self, tries: int) -> bool:

        logger.debug("Checking status on source")

        return self.__progress(
            f'//*[@id="src-status"]/{"span" if self.__bridge_name == "Skyline" else "div/div[2]"}'
            '//*[local-name()="svg"]//*[local-name()="path"]',
            tries
        )

    def __progress_bridge(self, tries: int) -> bool:

        logger.debug("Checking status on bridge")

        return self.__progress(
            f'//*[@id="bridge-status"]/{"span" if self.__bridge_name == "Skyline" else "div/div[2]"}'
            '//*[local-name()="svg"]//*[local-name()="path"]',
            tries
        )

    def __progress_destination(self, tries: int) -> bool:

        logger.debug("Checking status on destination")

        return self.__progress(
            f'//*[@id="dest-status"]/{"span" if self.__bridge_name == "Skyline" else "div/div[2]"}'
            '//*[local-name()="svg"]//*[local-name()="path"]',
            tries
        )

    def bridging(self, amount: str) -> None:

        if self.__source_wallet.get_subnetwork().lower() == ApexFusionSubnetwork.prime or \
                self.__source_wallet.get_subnetwork().lower() == ApexFusionSubnetwork.vector or \
                self.__source_wallet.get_subnetwork().lower() == CardanoSubnetwork.preview:

            logger.debug(f"Select the source wallet needed for the {self.__bridge_name} Bridge")

            self.__source_wallet.open_wallet()

        self.__open_bridge_app(
            self.__source_wallet.get_web_app_identifier(),
            self.__destination_wallet.get_web_app_identifier()
        )

        try:
            self.__sentry(getenv("SENTRY_ACCEPT", "False") == "True")
        except Exception:
            # can't find sentry dialog
            pass

        for _ in range(5):

            self.__connect_wallet()
            if self.__check_connected_wallet():
                break
            self.__disconnect_wallet()
            logger.debug(f"Retrying to connect {self.__source_wallet.get_subnetwork()} wallet to the {self.__bridge_name} Bridge")

        else:

            logger.critical(
                f"{self.__source_wallet.get_subnetwork()} wallet cannot be connected to the {self.__bridge_name} Bridge"
            )
            raise

        if self.__bridge_name != "Skyline":
            self.__move_funds()

        self.__destination_address(self.__destination_wallet.get_receive_address())
        self.__select_token()
        self.__amount_to_send(amount)
        self.__send_tx()
        self.__source_wallet.sign_and_confirm_transaction()

        if self.__bridge_name == "Skyline" and \
                self.__source_wallet.get_subnetwork().lower() != ApexFusionSubnetwork.prime and \
                self.__source_wallet.get_subnetwork().lower() != ApexFusionSubnetwork.vector and \
                self.__source_wallet.get_subnetwork().lower() != CardanoSubnetwork.preview and \
                self.__source_wallet.get_token_name().lower() == "mytesttoken":

            # Second transaction confirm
            self.__source_wallet.sign_and_confirm_transaction()

        if self.__bridge_name == "Skyline":

            # wait for the transaction to be processed and the tx_id to be available
            sleep(5)

            try:
                self.__tx_id = self.__get_tx_id()
            except Exception:
                pass

        logger.info(f"Start bridging {amount} {self.__source_wallet.get_token_name()}")

        try:

            for turn in [["initial", 1800], ["final", 10]]:

                logger.info(f"{turn[0].capitalize()} checks ⚙️")

                self.__is_source_succeeded = self.__progress_source(turn[1])

                logger.info(
                    f"{self.__source_wallet.get_subnetwork().capitalize()} "
                    f"{'✅' if self.__is_source_succeeded else '❌'}"
                )

                self.__is_bridge_succeeded = self.__progress_bridge(turn[1])

                logger.info(
                    f"Bridge "
                    f"{'✅' if self.__is_bridge_succeeded else '❌'}"
                )

                self.__is_destination_succeeded: bool = self.__progress_destination(turn[1])

                logger.info(
                    f"{self.__destination_wallet.get_subnetwork().capitalize()} "
                    f"{'✅' if self.__is_destination_succeeded else '❌'}"
                )

                logger.info(f"{turn[0].capitalize()} checks completed 🏁")

                if self.__is_source_succeeded and self.__is_bridge_succeeded and self.__is_destination_succeeded:
                    self.__final_status = "success"
                    break

                else:
                    self.__final_status = "failed"

        except Exception:
            # the progress status may occasionally fail to be detected,
            # but the implementation makes refreshing the page to retry checking the status impossible
            pass

        dump(
            obj={
                "tx_id": self.__tx_id,
                "status": self.__final_status,
                "source": self.__is_source_succeeded,
                "bridge": self.__is_bridge_succeeded,
                "destination": self.__is_destination_succeeded
            },
            fp=open(
                file="statuses.json",
                mode="w",
                encoding="utf-8"
            ),
            indent=4
        )

        logger.info(
            "Bridging "
            f"{'done successfully' if self.__final_status == 'success' else 'encountered issues'}"
        )
