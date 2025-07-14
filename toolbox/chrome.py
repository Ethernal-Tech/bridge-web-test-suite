from os import path
from time import sleep
from datetime import datetime
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
        print(f"{datetime.now()} - [INF] Starting ChromeDriver setup...")

        try:
            self.__extensions_dir_path: str = path.join(path.dirname(path.abspath(__file__)), 'extensions')

            self.__options = [
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--disable-popup-blocking"
                # "--disable-features=DisableLoadExtensionCommandLineSwitch" #Allow loading extensions in Chrome version >=137
            ]

            self.__chrome_options = Options()

            for arg in self.__options:
                self.__chrome_options.add_argument(arg)

            self.__chrome_options.add_extension(f'{self.__extensions_dir_path}/MetaMask.crx')

            if eternl_wallet_extension.lower() == 'beta':
                self.__chrome_options.add_extension(f'{self.__extensions_dir_path}/EternlBetaNew.crx')
            else:
                self.__chrome_options.add_extension(f'{self.__extensions_dir_path}/EternlNew.crx')

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

            caps = self.capabilities
            chrome_version = caps.get("browserVersion", "unknown")
            chromedriver_version = caps.get("chrome", {}).get("chromedriverVersion", "unknown").split(" ")[0]

            print(f"{datetime.now()} - [INF] Chrome version: {chrome_version}")
            print(f"{datetime.now()} - [INF] ChromeDriver version: {chromedriver_version}")

            print(f"{datetime.now()} - [INF] ChromeDriver initialized with MetaMask and Eternl({eternl_wallet_extension}) extension.")

        except Exception as e:
            print(f"{datetime.now()} - [ERR] Error during ChromeDriver setup: {e}")
            raise e
        
    def get_init_tab(self) -> str:
        return self.__init_tab

    def find_element_by_xpath(self, xpath: str) -> WebElement:
        return self.find_element(By.XPATH, xpath)
