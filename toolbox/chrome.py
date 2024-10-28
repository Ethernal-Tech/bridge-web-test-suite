from os import path
from glob import glob
from time import sleep
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver


class Chrome(WebDriver):
    def __init__(self) -> None:
        self.__logs: dict = dict()

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

        for ext in glob(f'{self.__extensions_dir_path}/*.crx'):
            self.__chrome_options.add_extension(ext)

        super().__init__(options=self.__chrome_options)

        # the first tab opened when chrome started
        self.__init_tab = self.current_window_handle

        # wait to chrome to open all startup tabs
        sleep(5)

    def get_init_tab(self) -> str:
        return self.__init_tab

    def add_to_log(self, key, value) -> None:
        self.__logs[key] = value

    def get_logs(self) -> dict:
        return self.__logs
