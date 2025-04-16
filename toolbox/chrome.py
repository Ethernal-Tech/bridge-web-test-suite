from os import path
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager


class Chrome(WebDriver):
    def __init__(
        self, 
        driver_version: str,
        eternl_wallet_extension: str
    ) -> None:

        self.__extensions_dir_path: str = path.join(path.dirname(path.abspath(__file__)), 'extensions')

        self.__options = [
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--disable-popup-blocking"
        ]

        self.__chrome_options = Options()

        for arg in self.__options:
            self.__chrome_options.add_argument(arg)

        self.__chrome_options.add_extension(f'{self.__extensions_dir_path}/MetaMask.crx')

        if eternl_wallet_extension.lower() == 'beta':
            self.__chrome_options.add_extension(f'{self.__extensions_dir_path}/EternlBeta.crx')
        else:
            self.__chrome_options.add_extension(f'{self.__extensions_dir_path}/Eternl.crx')

        self.__chrome_services = Service()
        self.__chrome_services.path = ChromeDriverManager(driver_version=driver_version).install()

        super().__init__(
            options=self.__chrome_options,
            service=self.__chrome_services
        )

        # the first tab opened when chrome started
        self.__init_tab = self.current_window_handle

        # wait to chrome to open all startup tabs
        sleep(5)

    def get_init_tab(self) -> str:
        return self.__init_tab

    def find_element_by_xpath(self, xpath: str) -> WebElement:
        return self.find_element(By.XPATH, xpath)
