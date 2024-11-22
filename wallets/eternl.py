from time import sleep
from datetime import datetime
from toolbox.chrome import Chrome
from toolbox.utils import retry, find_element_by_xpath
from selenium.common.exceptions import NoSuchElementException


class Eternl:
    def __init__(
            self,
            driver: Chrome,
            network: str,
            sign_key: str,
            name: str
    ) -> None:

        self.__url: str = 'chrome-extension://kmhcihpebfmpgmihbkipmjlmmioameka/index.html#/app/%s/welcome' % network
        self.__driver: Chrome = driver
        self.__sign_key: str = sign_key
        self.__name: str = name
        self.__receive_address: str = ""
        self.__balance: float = 0.0
        self.__opened_tabs: list[str] = self.__driver.window_handles

        self.__driver.switch_to.window(self.__driver.get_init_tab())

    @retry()
    def __add_wallet(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[3]/div[1]/button'
        ).click()

    @retry()
    def __restore_wallet(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[1]/div/main/div[2]/div[2]/div/div/div[1]/div[2]/button'
        ).click()

    @retry()
    def __recover_phrase(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[1]/div/main/div[2]/div[2]/div/div/div[1]/div/div/div[4]/button[1]'
        ).click()

        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[1]/div/main/div[2]/div[2]/div/div/div[1]/div/div/button'
        ).click()

    @retry()
    def __insert_recover_phrase(self, recover_phrase: str) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="wordInput"]'
        ).send_keys(recover_phrase)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[1]/div/main/div[2]/div[2]/div/div/div[1]/div/div/div/button[2]'
        ).click()

    @retry()
    def __set_wallet_name_and_sign_key(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="inputWalletName"]'
        ).send_keys(self.__name)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="password"]'
        ).send_keys(self.__sign_key)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="repeatPassword"]'
        ).send_keys(self.__sign_key)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="GridFormWalletNamePassword"]/button[3]'
        ).click()

    @retry()
    def __number_of_accounts(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="accountSelection"]/button[3]'
        ).click()

    @retry()
    def __open_wallet(self) -> None:
        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[3]/div[2]/nav/div/div[2]/div/div'
        ).click()

    @retry()
    def __set_receive_address(self) -> None:
        try:

            find_element_by_xpath(
                self.__driver,
                '//*[@id="cc-main-container"]/div/div[1]/div/main/div[1]/div/div[2]/nav/button[4]'
            ).click()

            receive_address = find_element_by_xpath(
                self.__driver,
                '//*[@id="cc-main-container"]/div/div[1]/div/main/div[2]/div[2]/div/div/div[1]/div[4]/div[1]/div/div'
            )

            self.__receive_address = receive_address.text.split('\n')[0]

        except NoSuchElementException:

            self.__driver.refresh()
            raise NoSuchElementException

    @retry()
    def __set_balance(self) -> None:
        balance = find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[1]/div/main/div[1]/div/div[1]/div/div[1]/div[2]/div[2]'
        ).text

        self.__balance = float(balance.split(maxsplit=1)[1].replace('\n', ''))

    def get_sign_key(self) -> str:
        return self.__sign_key

    def get_receive_address(self) -> str:
        return self.__receive_address

    def get_name(self) -> str:
        return self.__name

    def recover(self, recovery_phrase: str) -> None:
        print(f"{datetime.now()} Eternl Wallet '{self.__name}' start recovering")

        self.__driver.get(self.__url)
        self.__add_wallet()
        self.__restore_wallet()
        self.__recover_phrase()
        self.__insert_recover_phrase(recovery_phrase)
        self.__set_wallet_name_and_sign_key()
        self.__number_of_accounts()
        self.__open_wallet()
        self.__set_receive_address()

        print(f"{datetime.now()} Eternl Wallet '{self.__name}' recovered successfully")
        print(f'{datetime.now()} Receiver Address: {self.__receive_address}')

    @retry()
    def toggle(self) -> None:
        self.__driver.get(self.__url)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[3]/div[2]/nav/div/div[2]/div'
        ).click()

        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div[1]/div/main/div[1]/div/div[1]/div/div[3]'
        ).click()

    @retry()
    def grant_access(self) -> None:
        popup = list(set(self.__driver.window_handles) - set(self.__opened_tabs))[0]

        self.__driver.switch_to.window(popup)

        find_element_by_xpath(
            self.__driver,
            '//*[@id="cc-main-container"]/div/div/div/main/div/div[2]/button[2]'
        ).click()

        # wait access to be granted
        sleep(5)

        self.__driver.switch_to.window(self.__driver.get_init_tab())
