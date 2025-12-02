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
            source_wallet: Union[Eternl, MetaMask],
            destination_wallet: Union[Eternl, MetaMask]
    ) -> None:

        self.__bridge_name: str = bridge_name.capitalize()
        self.__bridge_url: str = path.join(getenv("BRIDGE_URL"), "app") if self.__bridge_name == "Skyline" else getenv("BRIDGE_URL")
        self.__apex_faucet_url: str = getenv("APEX_FUSION_FAUCET_URL")
        self.__driver: Chrome = driver
        self.__source_wallet: Union[Eternl, MetaMask] = source_wallet
        self.__destination_wallet: Union[Eternl, MetaMask] = destination_wallet
        self.__status_done: str = "M10.1042 16.9856L5.47772 12.3802L7.02501 10.8123L10.1042 13.8964L17.0119 " \
                                  "7.00977L18.559 8.55185L10.1042 16.9856Z"
        self.__is_source_succeeded: bool = False
        self.__is_bridge_succeeded: bool = False
        self.__is_destination_succeeded: bool = False
        self.__final_status: str = "Unknown"

        # TODO: Add support for Cardano Preview Faucet
        if self.__source_wallet.get_subnetwork() != CardanoSubnetwork.preview:
            self.__fund(self.__source_wallet.get_receive_address())

    @retry()
    def __fund(self, receiver_address: str) -> None:

        logger.debug(f"Getting funds from {self.__apex_faucet_url}")

        self.__driver.get(self.__apex_faucet_url)

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="address"]'
        ).send_keys(receiver_address)

        self.__driver.find_element_by_xpath(
            '//*[@id="app"]/div/div/div[2]/main/div/div[2]/div/div/form/div[2]/button'
        ).click()

        sleep(1)

        logger.debug(f"{receiver_address} has been funded")

    @retry()
    def __reject_sentry(self) -> None:

        if self.__bridge_name == "Skyline":

            logger.debug("Closing sentry dialog")

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[4]/div[4]/div/button[2]'
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

        self.__driver.execute_script(f"window.localStorage.setItem('selected_chain', '{source}');")
        self.__driver.execute_script(f"window.localStorage.setItem('destination_chain', '{destination}');")

        sleep(1)

        logger.debug("Source and destination chains set successfully")

        logger.debug(f"Reloading the {self.__bridge_name} Bridge")

        self.__driver.refresh()
        sleep(10)

        logger.debug(f"{self.__bridge_name} Bridge reloaded successfully")

    @retry(tries=5)
    def __connect_wallet_and_move_funds(self) -> None:

        if self.__bridge_name == "Skyline":

            logger.debug(
                f"Connecting {self.__source_wallet.get_subnetwork()} wallet "
                f"to the {self.__bridge_name} Bridge"
            )

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[3]/div/button'
            ).click()

            sleep(3)

            logger.debug(f"Moving funds to {self.__destination_wallet.get_subnetwork()}")

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[3]/div/button'
            ).click()

            sleep(1)

        else:

            logger.debug(
                f"Connecting {self.__source_wallet.get_subnetwork()} wallet "
                f"to the {self.__bridge_name} Bridge"
            )

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/button'
            ).click()

            sleep(3)

            logger.debug(f"Moving funds to {self.__destination_wallet.get_subnetwork()}")

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/button'
            ).click()

            sleep(1)

    @retry()
    def __destination_address(self, destination_address: str) -> None:

        logger.debug(f"Inserting destination address as {self.__destination_wallet.get_receive_address()}")

        if self.__bridge_name == "Skyline":

            self.__driver.find_element_by_xpath(
                '/html/body/div/div[1]/'
                'div[3]/div/div/div[4]/div/div[2]/div/div/input'
            ).send_keys(destination_address)

        else:

            self.__driver.find_element_by_xpath(
                '/html/body/div/div[1]/'
                'div[2]/div/div/div[4]/div/div[2]/div/div/input'
            ).send_keys(destination_address)

        logger.debug("The Destination address inserted successfully")

        sleep(1)

    @retry()
    def __select_token(self) -> None:

        if self.__bridge_name == "Skyline":

            logger.debug(f"Selecting source token as {self.__source_wallet.get_token_name().upper()}")

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[3]/div/div/div[4]/div/div[3]/div'
            ).click()

            sleep(1)

            self.__driver.find_element_by_xpath(
                f'//*[starts-with(@id, "menu")]'
                f'//*[translate(text(), '
                f'"ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
                f'"abcdefghijklmnopqrstuvwxyz") = '
                f'"{self.__source_wallet.get_token_name()}"]'
            ).click()

            logger.debug("Source token selected")

            sleep(1)

    @retry()
    def __amount_to_send(self, amount: str) -> None:

        logger.debug(f"Inserting {amount} tokens to be bridged")

        if self.__bridge_name == "Skyline":

            self.__driver.find_element_by_xpath(
                '/html/body/div/div[1]/'
                'div[3]/div/div/div[4]/div/'
                'div[4]/div[1]/div/div/div/input'
            ).send_keys(amount)

        else:

            self.__driver.find_element_by_xpath(
                '/html/body/div/div[1]/'
                'div[2]/div/div/div[4]/div/'
                'div[3]/div[1]/div/div/div/input'
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

        if self.__bridge_name == "Skyline":

            self.__driver.find_element_by_xpath(
                '/html/body/div/div[1]/div[3]/div/div/div[4]/div/div[4]/button[2]'
            ).click()

        else:

            self.__driver.find_element_by_xpath(
                '//*[@id="root"]/div[1]/div[2]/div/div/div[4]/div/div[3]/button[2]'
            ).click()

        sleep(5)

    @retry()
    def __progress(self, xpath1: str, xpath2: str, tries: int = 1800) -> bool:

        logger.debug("Getting progress status every 1sec")

        while tries > 0:

            try:

                status = self.__driver.find_element_by_xpath(xpath1).get_attribute("d")

                if status == self.__status_done:

                    logger.debug("Progress is done")

                    return True

            except NoSuchElementException:

                try:

                    status = self.__driver.find_element_by_xpath(xpath2).get_attribute("d")

                    if status == self.__status_done:
                        logger.debug("Progress is done")

                        return True

                except NoSuchElementException:

                    pass

                pass

            tries -= 1

            logger.debug("Progress is not done yet")
            logger.debug(f"Remaining progress status tries: {tries}")

            sleep(1)

        return False

    def __progress_source(self) -> bool:

        logger.debug("Checking status on source")

        if self.__bridge_name == "Skyline":

            return self.__progress(
                '//*[@id="root"]/div[1]/div[3]/div/div[2]/div[4]/div/div[1]/div[1]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]',
                '//*[@id="root"]/div[1]/div[3]/div/div[2]/div[2]/div/div[1]/div[1]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]'
            )

        else:

            return self.__progress(
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/div[4]/div/div[1]/div[1]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]',
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/div[2]/div/div[1]/div[1]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]'
            )

    def __progress_bridge(self) -> bool:

        logger.debug("Checking status on bridge")

        if self.__bridge_name == "Skyline":

            return self.__progress(
                '//*[@id="root"]/div[1]/div[3]/div/div[2]/div[4]/div/div[1]/div[2]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]',
                '//*[@id="root"]/div[1]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]'
            )

        else:

            return self.__progress(
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/div[4]/div/div[1]/div[2]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]',
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/div[2]/div/div[1]/div[2]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]'
            )

    def __progress_destination(self) -> bool:

        logger.debug("Checking status on destination")

        if self.__bridge_name == "Skyline":

            return self.__progress(
                '//*[@id="root"]/div[1]/div[3]/div/div[2]/div[2]/div/div[1]/div[3]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]',
                '//*[@id="root"]/div[1]/div[3]/div/div[2]/div[2]/div/div[1]/div[3]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]'
            )

        else:

            return self.__progress(
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/div[2]/div/div[1]/div[3]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]',
                '//*[@id="root"]/div[1]/div[2]/div/div[2]/div[2]/div/div[1]/div[3]/div/div[2]'
                '//*[local-name()="svg"]//*[local-name()="path"]'
            )

    def bridging(self, amount: str) -> None:

        if self.__source_wallet.get_subnetwork() != ApexFusionSubnetwork.nexus:

            logger.debug(f"Select the source wallet needed for the {self.__bridge_name} Bridge")

            self.__source_wallet.open_wallet()

        self.__open_bridge_app(
            self.__source_wallet.get_web_app_identifier(),
            self.__destination_wallet.get_web_app_identifier()
        )

        self.__reject_sentry()

        self.__connect_wallet_and_move_funds()
        self.__destination_address(self.__destination_wallet.get_receive_address())
        self.__select_token()
        self.__amount_to_send(amount)
        self.__send_tx()
        self.__source_wallet.sign_and_confirm_transaction()

        logger.info(f"Start bridging {amount} {self.__source_wallet.get_token_name().upper()}")

        try:

            self.__is_source_succeeded = self.__progress_source()

            logger.info(
                f"{self.__source_wallet.get_subnetwork().capitalize()} "
                f"{'✅' if self.__is_source_succeeded else '❌'}"
            )
            
            self.__is_bridge_succeeded = self.__progress_bridge()

            logger.info(
                f"Bridge "
                f"{'✅' if self.__is_bridge_succeeded else '❌'}"
            )
            
            self.__is_destination_succeeded: bool = self.__progress_destination()

            logger.info(
                f"{self.__destination_wallet.get_subnetwork().capitalize()} "
                f"{'✅' if self.__is_destination_succeeded else '❌'}"
            )

            if self.__is_source_succeeded and self.__is_bridge_succeeded and self.__is_destination_succeeded:

                self.__final_status = "success"

            else:

                self.__final_status = "failed"

        except Exception:
            # the progress status may occasionally fail to be detected,
            # but the implementation makes refreshing the page to retry checking the status impossible
            pass

        dump(
            obj={
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

        logger.info("Bridging done successfully")
