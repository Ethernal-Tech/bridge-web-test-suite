from time import sleep
from requests import get
from zipfile import ZipFile
from subprocess import run, DEVNULL
from os import getenv, path, remove, listdir
from shutil import copyfileobj, rmtree, move
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from toolbox.logger import logger
from toolbox.utils import retry


class Chrome(WebDriver):
    def __init__(self) -> None:

        logger.debug("Starting Chrome setup")

        try:

            # Set Chrome Options flags
            self.__options: [str] = [
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--disable-popup-blocking",
                "--disable-features=DisableLoadExtensionCommandLineSwitch"
            ]

            # Pre-configured Chrome profile with ready-to-use Metamask wallet and Eternl wallet
            # Also, Reactor Bridge and Skyline Bridge permissions already setup
            if getenv("CHROME_CONFIGS_URL"):

                logger.debug("Downloading Chrome Configs")

                config = get(getenv("CHROME_CONFIGS_URL"), stream=True)
                with open("/tmp/bridge-web-test-suite.zip", "wb") as f:
                    copyfileobj(config.raw, f)

                logger.debug("The Chrome Configs downloaded successfully")
                logger.debug("Extracting the Chrome Configs")

                if path.exists("/tmp/bridge-web-test-suite"):
                    rmtree("/tmp/bridge-web-test-suite")

                with ZipFile("/tmp/bridge-web-test-suite.zip", "r") as z:
                    z.extractall("/tmp/")

                remove("/tmp/bridge-web-test-suite.zip")

                for lock_file in ("DevToolsActivePort", "SingletonLock", "SingletonSocket", "SingletonCookie"):
                    lock_path = path.join("/tmp/bridge-web-test-suite", lock_file)
                    if path.isdir(lock_path):
                        rmtree(lock_path)
                    elif path.lexists(lock_path):
                        remove(lock_path)

                self.__options.append("user-data-dir=/tmp/bridge-web-test-suite")
                self.__options.append("profile-directory=Default")

                logger.debug("The Chrome Configs extracted successfully")

            self.__chrome_options: Options = Options()

            if getenv("LOCAL_TEST") == "True":

                logger.debug("Downloading Chrome For Testing")

                app = get(getenv("CHROME_URL"), stream=True)
                with open("chrome.zip", "wb") as f:
                    copyfileobj(app.raw, f)

                logger.debug("The Chrome For Testing downloaded successfully")
                logger.debug("Extracting the Chrome For Testing")

                chrome_path: str = path.join(path.dirname(path.abspath(__file__)), "chrome")

                if path.exists(chrome_path):
                    rmtree(chrome_path)

                with ZipFile("chrome.zip", "r") as z:
                    z.extractall("chrome_tmp")

                for directory in listdir("chrome_tmp"):
                    move(path.join("chrome_tmp", directory), chrome_path)

                logger.debug("Fix permission for the Chrome For Testing")

                run(
                    args=[
                        "sudo",
                        "-S",
                        "xattr",
                        "-r",
                        "-d",
                        "com.apple.quarantine",
                        path.join(chrome_path, "Google Chrome for Testing.app")
                    ],
                    check=True,
                    input=getenv("SUDO").encode(),
                    stderr=DEVNULL
                )

                run(
                    args=[
                        "sudo",
                        "-S",
                        "chmod",
                        "-R",
                        "+x",
                        path.join(chrome_path, "Google Chrome for Testing.app")
                    ],
                    check=True,
                    input=getenv("SUDO").encode(),
                    stderr=DEVNULL
                )

                rmtree("chrome_tmp")
                remove("chrome.zip")

                self.__chrome_options.binary_location = path.join(
                    chrome_path,
                    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
                )

                logger.debug("The Chrome For Testing extracted successfully")

            for arg in self.__options:

                self.__chrome_options.add_argument(arg)
                logger.debug(f"{arg} added to Chrome Options")

            # Add extensions
            self.__extensions_dir_path: str = path.join(path.dirname(path.abspath(__file__)), "extensions")
            self.__chrome_options.add_extension(path.join(self.__extensions_dir_path, "MetaMask.crx"))
            self.__chrome_options.add_extension(path.join(self.__extensions_dir_path, "Eternl.crx"))

            self.__chrome_services: Service = Service()

            logger.debug("Installing Chrome Driver")

            self.__chrome_services.path = ChromeDriverManager(
                driver_version=getenv("CHROMEDRIVER_VERSION")
            ).install()

            logger.debug(f"Chrome Driver v{self.__chrome_services.path.split('/')[-3]} installed successfully")

            logger.debug("Starting Chrome")

            super().__init__(
                options=self.__chrome_options,
                service=self.__chrome_services
            )

            # The first tab opened when chrome started
            self.__init_tab: str = self.current_window_handle

            # Wait to chrome to open all startup tabs
            sleep(5)

            logger.debug(
                f"Chrome v{self.capabilities['browserVersion']} "
                f"with Chrome Driver v{self.capabilities['chrome']['chromedriverVersion'].split()[0]} "
                f"is running"
            )

            logger.debug("Chrome setup completed successfully")

        except Exception as e:

            logger.critical(e, exc_info=True)

            raise

    def get_init_tab(self) -> str:

        return self.__init_tab

    def find_element_by_xpath(self, xpath: str) -> WebElement:

        return self.find_element(By.XPATH, xpath)

    @retry()
    def bypass_input_protection(self, element: WebElement, value: str) -> None:

        logger.debug("Bypassing input protection")

        try:

            self.execute_script(
                """
                const el = arguments[0];
                const val = arguments[1];

                if (el.hasAttribute('contenteditable')) {
                    el.innerHTML = val;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    return;
                }

                const lastValue = el.value;
                el.value = val;
                const tracker = el._valueTracker;

                if (tracker) {
                    tracker.setValue(lastValue);
                }

                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                value
            )

            new_value = self.execute_script(
                "return arguments[0].value || arguments[0].innerHTML",
                element
            )

            if value not in new_value:

                logger.error("Error while bypassing input protection")
                logger.error(f"Expected value: {value}")
                logger.error(f"Returned value: {new_value}")

                raise ValueError

        except Exception as e:

            logger.error(e, exc_info=True)

            raise

        logger.debug("Bypassed input protection successfully")
