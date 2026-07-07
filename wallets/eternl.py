from time import sleep
from toolbox.chrome import Chrome
from toolbox.logger import logger
from toolbox.utils import Network, retry
from selenium.common.exceptions import NoSuchElementException


class Eternl:
    def __init__(
            self,
            driver: Chrome,
            network: str,
            subnetwork: str,
            token_name: str,
            connect: str,
            sign_key: str
    ) -> None:

        self.__extension_url: str = "chrome-extension://kmhcihpebfmpgmihbkipmjlmmioameka"
        self.__url: str = f"{self.__extension_url}/index.html#/{connect}/wallet/home"
        self.__sign_tx_url: str = f"{self.__extension_url}/app/signTx.html"
        self.__receive_url: str = f"{self.__extension_url}/index.html#/{connect}/wallet/receive"
        self.__driver: Chrome = driver
        self.__network: str = network
        self.__subnetwork: str = subnetwork
        self.__token_name: str = token_name
        self.__sign_key: str = sign_key
        self.__receive_address: str = ""
        self.__opened_tabs: list[str] = self.__driver.window_handles

        self.__driver.switch_to.window(self.__driver.get_init_tab())

        self.open_wallet()
        self.__set_receive_address()

    @retry()
    def __set_receive_address(self) -> None:

        logger.debug(f"Setting {self.__subnetwork.capitalize()} address")

        for i in range(10):

            self.__driver.get(self.__receive_url)

            sleep(3)

            self.__driver.find_element_by_xpath(
                '/html/body/div[1]/div[2]/div[1]/div'
                '/div[2]/main/div/div/div/div/div/div[2]/div/div[1]/div/div/div[2]/div/div[2]/button'
            ).click()

            sleep(2)

            self.__receive_address = self.__driver.find_element_by_xpath(
                '/html/body/div[3]/div/div/div/div[2]/div/div[1]'
            ).text

            if len(self.__receive_address) > 0 and '.' not in self.__receive_address:

                logger.info(f"{self.__subnetwork.capitalize()} address: {self.__receive_address}")

                break

            logger.error(f"{self.__subnetwork.capitalize()} address is unknown")

            raise ValueError

        else:

            logger.critical(f"Failed to set {self.__subnetwork.capitalize()} address")

            raise ValueError

    @retry()
    def open_wallet(self) -> None:

        logger.debug(f"Opening {self.__subnetwork.capitalize()} wallet at {self.__url}")

        self.__driver.get(self.__url)
        sleep(10)

        for i in range(10):

            try:

                # Checking if the page is fully loaded
                self.__driver.find_element_by_xpath(
                    '/html/body/div[1]/div[2]/div[1]/div'
                    '/div[1]/div[1]/div/div[2]/div/div/button[7]'
                )

                logger.debug(f"{self.__subnetwork.capitalize()} wallet url opened successfully")

                break

            except NoSuchElementException:

                logger.error(f"{self.__subnetwork.capitalize()} wallet is not fully loaded")
                self.__driver.refresh()
                sleep(10)
                pass

        else:

            logger.critical(f"Failed to load {self.__subnetwork.capitalize()} wallet")

            raise ValueError

    @retry()
    def sign_and_confirm_transaction(self) -> None:

        logger.debug("Opening Sign Tx element in new Chrome tab")

        self.__driver.switch_to.new_window(type_hint="tab")
        popup = list(set(self.__driver.window_handles) - set(self.__opened_tabs))[0]
        self.__driver.switch_to.window(popup)
        self.__driver.get(self.__sign_tx_url)

        logger.debug("The Sign Tx element opened successfully")

        sleep(5)

        logger.debug(f"Inserting Sign Key for {self.__subnetwork} wallet")

        # Note: Using XPath by ID is not an option
        # because the same ID appears twice
        # and the one retrieved is incorrect
        self.__driver.find_element_by_xpath(
            '/html/body/div/div[3]/div[18]/div[2]/div/div[2]/div[2]/div[2]/div/div/div/div[4]/'
            'div[1]/div[1]/div/span/div/input'
        ).send_keys(self.__sign_key)

        logger.debug("The Sign Key inserted successfully")

        sleep(1)

        logger.debug("Start confirming transaction")

        self.__driver.find_element_by_xpath(
            '/html/body/div/div[3]/div[18]/div[2]/div/div[2]/div[2]/div[2]/div/div/div/div[4]/'
            'div[2]/button[2]'
        ).click()

        # wait for the transaction to be signed
        sleep(5)

        logger.debug("The transaction confirmed successfully")

        self.__driver.close()
        self.__driver.switch_to.window(self.__driver.get_init_tab())

    def get_receive_address(self) -> str:

        return self.__receive_address

    def get_subnetwork(self) -> str:

        return self.__subnetwork

    def get_web_app_identifier(self) -> str:

        return self.__subnetwork if self.__network == Network.apex else self.__network

    def get_token_name(self) -> str:

        return self.__token_name
