from time import sleep
from toolbox.chrome import Chrome
from toolbox.logger import logger
from toolbox.utils import retry
from selenium.common.exceptions import NoSuchElementException


class MetaMask:
    def __init__(
            self,
            driver: Chrome,
            sign_key: str,
            subnetwork: str,
            token_name: str
    ) -> None:

        self.__extension_url: str = "chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn"
        self.__url: str = f"{self.__extension_url}/home.html"
        self.__notification_url: str = f"{self.__extension_url}/notification.html"
        self.__driver: Chrome = driver
        self.__sign_key: str = sign_key
        self.__subnetwork: str = subnetwork
        self.__token_name: str = token_name
        self.__receive_address: str = ""
        self.__opened_tabs: list[str] = self.__driver.window_handles

        self.__driver.switch_to.window(self.__driver.get_init_tab())

        self.open_wallet()
        self.__unlock()
        self.__set_receive_address()

    @retry()
    def __unlock(self) -> None:

        logger.debug("Unlocking Metamask")

        sleep(5)

        self.__driver.bypass_input_protection(
            self.__driver.find_element_by_xpath(
                '//*[@id="password"]'
            ),
            self.__sign_key
        )

        self.__driver.find_element_by_xpath(
            '//*[@id="app-content"]/div/div/div/form/div/button[1]'
        ).click()

        logger.debug("Metamask unlocked successfully")

    @retry()
    def __set_receive_address(self) -> None:

        logger.debug(f"Setting {self.__subnetwork.capitalize()} address")

        for i in range(10):

            self.__driver.get(self.__url)

            sleep(5)

            self.__driver.find_element_by_xpath(
                '//*[@id="app-content"]/div/div[2]/div/div[2]/div/div/button'
            ).click()

            self.__driver.find_element_by_xpath(
                '//*[@id="app-content"]/div/div[2]/div/div[2]/div[2]/button[2]'
            ).click()

            self.__driver.find_element_by_xpath(
                '//*[@id="app-content"]/div/div/div/div/div[2]/div[2]/div[2]'
            ).click()

            self.__receive_address = self.__driver.execute_script(
                "return arguments[0].textContent;",
                self.__driver.find_element_by_xpath('//*[@id="app-content"]/div/div/div/div/div[2]/div/p[2]')
            )

            if len(self.__receive_address) > 0:

                logger.info(f"{self.__subnetwork.capitalize()} address: {self.__receive_address}")

                break

            logger.error(f"{self.__subnetwork.capitalize()} address is unknown")

        else:

            logger.critical(f"Failed to set {self.__subnetwork.capitalize()} address")

            raise ValueError

    @retry()
    def open_wallet(self) -> None:

        logger.debug(f"Opening {self.__subnetwork.capitalize()} wallet at {self.__url}")

        self.__driver.get(self.__url)
        sleep(5)

        for i in range(10):

            try:

                # Checking if the page is fully loaded
                self.__driver.find_element_by_xpath(
                    '/html/body/div[1]/div/div/div/form/div/h1'
                )

                logger.debug(f"{self.__subnetwork.capitalize()} wallet url opened successfully")

                break

            except NoSuchElementException:

                logger.error(f"{self.__subnetwork.capitalize()} wallet is not fully loaded")
                self.__driver.refresh()
                sleep(5)
                pass

        else:

            logger.critical(f"Failed to load {self.__subnetwork.capitalize()} wallet")

            raise ValueError

    @retry()
    def sign_and_confirm_transaction(self) -> None:

        logger.debug("Opening transaction confirmation element in new Chrome tab")

        self.__driver.switch_to.new_window(type_hint="tab")
        popup = list(set(self.__driver.window_handles) - set(self.__opened_tabs))[0]
        self.__driver.switch_to.window(popup)
        self.__driver.get(self.__notification_url)

        sleep(5)

        self.__driver.find_element_by_xpath(
            '//*[@id="app-content"]/div/div/div/div/div[3]/div/button[2]'
        ).click()

        # wait for the transaction to be confirmed
        sleep(5)

        logger.debug("The transaction confirmation done successfully")

        self.__driver.close()
        self.__driver.switch_to.window(self.__driver.get_init_tab())

    def get_receive_address(self) -> str:

        return self.__receive_address

    def get_subnetwork(self) -> str:

        return self.__subnetwork

    def get_web_app_identifier(self) -> str:

        return self.__subnetwork

    def get_token_name(self) -> str:

        return self.__token_name
