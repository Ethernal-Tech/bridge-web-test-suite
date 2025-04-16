from time import sleep
from datetime import datetime
from toolbox.chrome import Chrome
from toolbox.utils import Network, retry
from toolbox.utils import ApexFusionSubnetwork
from selenium.common.exceptions import NoSuchElementException


class Eternl:
    def __init__(
            self,
            driver: Chrome,
            network: str,
            subnetwork: str,
            token_name: str,
            connect: str,
            sign_key: str,
            extension: str
    ) -> None:

        self.__extension: str = 'aafgiaaomjbkmgainbdgjpcndnodkajp' if extension.lower() == 'beta' else 'kmhcihpebfmpgmihbkipmjlmmioameka'
        self.__url: str = 'chrome-extension://%s/index.html#/%s/wallet/home' % (self.__extension, connect)
        self.__driver: Chrome = driver
        self.__network: str = network
        self.__subnetwork: str = subnetwork
        self.__token_name: str = token_name
        self.__sign_key: str = sign_key
        self.__receive_address: str = ""
        self.__opened_tabs: list[str] = self.__driver.window_handles

        self.__driver.switch_to.window(self.__driver.get_init_tab())

    @retry(tries=5)
    def __open_app(self) -> None:
        sleep(3)

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-modal"]/div/div/div/div[2]/div[4]/div/button'
        ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="modalSetupSettingsFooter"]/button'
        ).click()

        sleep(1)

        if self.__network == Network.cardano:

            self.__driver.find_element_by_xpath(
                '//*[@id="modal-network-select"]/div/div/div/div[2]/div[3]/div/div/div[2]/div/button[3]'
            ).click()

        elif self.__network == Network.apex:

            self.__driver.find_element_by_xpath(
                '//*[@id="modal-network-select"]/div/div/div/div[2]/div[3]/div/div/div[1]/button[2]'
            ).click()

            sleep(1)

            if self.__subnetwork == ApexFusionSubnetwork.prime:

                self.__driver.find_element_by_xpath(
                    '//*[@id="modal-network-select"]/div/div/div/div[2]/div[3]/div/div/div[2]/div/button[3]'
                ).click()

            elif self.__subnetwork == ApexFusionSubnetwork.vector:

                self.__driver.find_element_by_xpath(
                    '//*[@id="modal-network-select"]/div/div/div/div[2]/div[3]/div/div/div[2]/div/button[2]'
                ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="modelSetupSettingsBtnNext"]'
        ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="modalSetupSettingsFooter"]/div/button[1]'
        ).click()

        sleep(5)

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-modal"]/div[2]/div/div/div[2]/div[4]/div/button'
        ).click()

    @retry()
    def __restore_wallet(self) -> None:
        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-modal"]/div/div/div/div[2]/div[5]/div/div/button[3]'
        ).click()

        sleep(3)

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-modal"]/div/div/div/div[2]/div[3]/div/div/div/button[1]'
        ).click()

    @retry()
    def __insert_recover_phrase(self, recover_phrase: str) -> None:
        sleep(1)

        for index, word in enumerate(recover_phrase.split()):

            self.__driver.find_element_by_xpath(
                f'//*[@id="word{index}"]'
            ).send_keys(word)

            sleep(1)

            self.__driver.find_element_by_xpath(
                '//*[@id="eternl-modal"]/div/div/div/div[2]/div[1]'
            ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="modelRestoreWalletBtnNext"]'
        ).click()

    @retry()
    def __set_wallet_name_and_sign_key(self) -> None:
        self.__driver.find_element_by_xpath(
            '//*[@id="walletName"]'
        ).send_keys(self.__subnetwork)

        self.__driver.find_element_by_xpath(
            '//*[@id="modelRestoreWalletBtnNext"]'
        ).click()

        sleep(1)

        self.__driver.find_element_by_xpath(
            '//*[@id="password"]'
        ).send_keys(self.__sign_key)

        self.__driver.find_element_by_xpath(
            '//*[@id="passwordConfirm"]'
        ).send_keys(self.__sign_key)

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-sign-derivation"]/div/div/div/div[2]'
        ).click()

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-sign-derivation"]/div/div/div/div[2]/div[3]/div/div/div[2]/div[2]/button[2]'
        ).click()

        sleep(10)

    @retry()
    def __number_of_accounts(self) -> None:
        self.__driver.find_element_by_xpath(
            '//*[@id="modelRestoreWalletBtnNext"]'
        ).click()

    @retry()
    def __set_receive_address(self) -> None:
        try:

            self.__driver.find_element_by_xpath(
                '//*[@id="eternl-app"]/div[2]/div[1]/div/div[1]/div[2]/nav/div/div[1]/div/div/button[3]'
            ).click()

            sleep(1)

            self.__driver.find_element_by_xpath(
                '//*[@id="eternl-app"]/div[2]/div[1]/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div/div/div[2]/div/div/div/div/div[2]/button'
            ).click()

            sleep(1)

            self.__driver.find_element_by_xpath(
                '//*[@id="eternl-app"]/div[2]/div[1]/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div/div/div[2]/div/div/div/div/div[2]/div/div/button'
            ).click()

            sleep(2)

            receive_address = self.__driver.find_element_by_xpath(
                '/html/body/div[3]/div/div/div/div[2]/div/div[1]'
            )

            self.__receive_address = receive_address.text

        except NoSuchElementException:

            self.__driver.refresh()
            raise NoSuchElementException

    def get_sign_key(self) -> str:
        return self.__sign_key

    def get_receive_address(self) -> str:
        return self.__receive_address

    def get_subnetwork(self) -> str:
        return self.__subnetwork

    def get_web_app_identifier(self) -> str:
        return self.__subnetwork if self.__network == Network.apex else self.__network

    def get_token_name(self) -> str:
        return self.__token_name

    def recover(self, recovery_phrase: str) -> None:
        print(f"{datetime.now()} Start recovering {self.__subnetwork} wallet")

        self.__driver.get(self.__url)

        try:
            self.__open_app()
        except NoSuchElementException:
            # Only when opening the Eternl Wallet for the first time
            pass

        self.__restore_wallet()
        self.__insert_recover_phrase(recovery_phrase)
        self.__number_of_accounts()
        self.__set_wallet_name_and_sign_key()
        self.__set_receive_address()

        print(f"{datetime.now()} {self.__subnetwork.capitalize()} wallet recovered successfully")
        print(f'{datetime.now()} {self.__subnetwork.capitalize()} address: {self.__receive_address}')

    @retry()
    def toggle(self) -> None:
        self.__driver.get(self.__url)

    @retry()
    def grant_access(self) -> None:
        popup = list(set(self.__driver.window_handles) - set(self.__opened_tabs))[0]

        self.__driver.switch_to.window(popup)

        self.__driver.find_element_by_xpath(
            '//*[@id="eternl-enable"]/div/div/div/div[2]/div[4]/div/button[2]'
        ).click()

        # wait access to be granted
        sleep(5)

        self.__driver.switch_to.window(self.__driver.get_init_tab())
