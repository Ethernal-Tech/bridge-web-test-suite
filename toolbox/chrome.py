import os
import json
import struct
from time import sleep
from base64 import b64encode
from hashlib import sha256
from pathlib import Path
from requests import get
from zipfile import ZipFile
from xattr import removexattr
from platform import system, machine
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
            self.__options: list[str] = [
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--disable-popup-blocking",
                "--disable-features=DisableLoadExtensionCommandLineSwitch",
                "--remote-allow-origins=*"
            ]

            # Pre-configured Chrome profile with ready-to-use Metamask wallet and Eternl wallet
            # Also, Reactor Bridge and Skyline Bridge permissions already setup
            if os.getenv("CHROME_CONFIGS_URL"):

                logger.debug("Downloading Chrome Configs")

                config = get(os.getenv("CHROME_CONFIGS_URL"), stream=True)
                with open("/tmp/bridge-web-test-suite.zip", "wb") as f:
                    copyfileobj(config.raw, f)

                logger.debug("The Chrome Configs downloaded successfully")
                logger.debug("Extracting the Chrome Configs")

                if os.path.exists("/tmp/bridge-web-test-suite"):
                    rmtree("/tmp/bridge-web-test-suite")

                with ZipFile("/tmp/bridge-web-test-suite.zip", "r") as z:
                    z.extractall("/tmp/")

                os.remove("/tmp/bridge-web-test-suite.zip")

                # Remove lock files to avoid Chrome startup issues
                for lock_file in ("DevToolsActivePort", "SingletonLock", "SingletonSocket", "SingletonCookie"):
                    lock_path = os.path.join("/tmp/bridge-web-test-suite", lock_file)
                    if os.path.isdir(lock_path):
                        rmtree(lock_path)
                    elif os.path.lexists(lock_path):
                        os.remove(lock_path)

                self.__options.append("user-data-dir=/tmp/bridge-web-test-suite")
                self.__options.append("profile-directory=Default")

                logger.debug("The Chrome Configs extracted successfully")

            self.__chrome_options: Options = Options()

            os_name: str = system()
            logger.debug(f"Operating system: {os_name}")

            if os_name == "Darwin":
                platform: str = "mac-arm64" if machine() == "arm64" else "mac-x64"
            elif os_name == "Linux":
                platform: str = "linux64"
            else:
                raise RuntimeError(f"Unsupported operating system: {os_name}")

            logger.debug(f"Platform: {platform}")

            logger.debug("Downloading Chrome For Testing")

            desired_chrome_version: str = os.getenv("CHROME_VERSION")

            chrome_versions: dict = get(
                "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            ).json()

            for v in chrome_versions["versions"]:
                if v["version"] == desired_chrome_version:
                    for d in v["downloads"]["chrome"]:
                        if d["platform"] == platform:
                            chrome_url: str = d["url"]
                            break
                    break

            app = get(chrome_url, stream=True)

            with open("chrome.zip", "wb") as f:
                copyfileobj(app.raw, f)

            logger.debug("The Chrome For Testing downloaded successfully")

            logger.debug("Extracting the Chrome For Testing")

            chrome_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome")

            if os.path.exists(chrome_path):
                rmtree(chrome_path)

            with ZipFile("chrome.zip", "r") as z:
                z.extractall("chrome_tmp")

            for directory in os.listdir("chrome_tmp"):
                move(os.path.join("chrome_tmp", directory), chrome_path)

            logger.debug("Fix permission for the Chrome For Testing")

            if os_name == "Darwin":

                app_path = os.path.join(chrome_path, "Google Chrome for Testing.app")

                for target in [app_path, *Path(app_path).rglob("*")]:

                    try:
                        removexattr(str(target), "com.apple.quarantine")
                    except OSError:
                        pass

                    os.chmod(target, 0o755)

                self.__chrome_options.binary_location = os.path.join(
                    chrome_path,
                    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
                )

            elif os_name == "Linux":

                for target in Path(chrome_path).rglob("*"):
                    os.chmod(target, 0o755)

                self.__chrome_options.binary_location = os.path.join(
                    chrome_path, 
                    "chrome"
                )

            else:
                raise RuntimeError(f"Unsupported operating system: {os_name}")

            rmtree("chrome_tmp")
            os.remove("chrome.zip")

            logger.debug("The Chrome For Testing extracted successfully")

            for arg in self.__options:

                self.__chrome_options.add_argument(arg)
                logger.debug(f"{arg} added to Chrome Options")

            # Add extensions
            self.__extensions_dir_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extensions")

            extension_paths: list[str] = []

            for crx in ("MetaMask.crx", "Eternl.crx", "Phantom.crx"):

                crx_path: str = os.path.join(self.__extensions_dir_path, crx)
                extension_paths.append(self.__unpack_crx(crx_path, "/tmp/bridge-web-test-suite-extensions"))

            # Chrome honors only the last --load-extension switch, so all paths go into a single comma-separated one
            load_extension_arg: str = f"--load-extension={','.join(extension_paths)}"
            self.__chrome_options.add_argument(load_extension_arg)
            logger.debug(f"{load_extension_arg} added to Chrome Options")

            self.__chrome_services: Service = Service()

            logger.debug("Installing Chrome Driver")

            self.__chrome_services.path = ChromeDriverManager(
                driver_version=os.getenv("CHROMEDRIVER_VERSION")
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
            sleep(10)

            logger.debug(
                f"Chrome v{self.capabilities['browserVersion']} "
                f"with Chrome Driver v{self.capabilities['chrome']['chromedriverVersion'].split()[0]} "
                f"is running"
            )

            logger.debug("Chrome setup completed successfully")

        except Exception as e:

            logger.critical(e, exc_info=True)

            raise

    @staticmethod
    def __protobuf_fields(data: bytes):

        # Minimal protobuf reader for the CRX3 header (only length-delimited fields are used there)
        def varint(i: int) -> tuple[int, int]:

            result = shift = 0

            while True:
                byte = data[i]
                i += 1
                result |= (byte & 0x7f) << shift
                shift += 7
                if not byte & 0x80:
                    return result, i

        i = 0

        while i < len(data):
            tag, i = varint(i)
            length, i = varint(i)
            yield tag >> 3, data[i:i + length]
            i += length

    def __unpack_crx(self, crx_path: str, target_dir: str) -> str:

        # Unpack a CRX3 file and add its public key to manifest.json,
        # so the unpacked extension keeps the same ID as the packed one
        with open(crx_path, "rb") as f:
            data = f.read()

        if data[:4] != b"Cr24" or struct.unpack("<I", data[4:8])[0] != 3:
            raise ValueError(f"{crx_path} is not a CRX3 file")

        header_size: int = struct.unpack("<I", data[8:12])[0]
        header: bytes = data[12:12 + header_size]

        public_keys: list[bytes] = []
        crx_id: bytes = b""

        for field, value in self.__protobuf_fields(header):
            if field in (2, 3):  # sha256_with_rsa, sha256_with_ecdsa
                public_keys.append(dict(self.__protobuf_fields(value))[1])
            elif field == 10000:  # signed_header_data
                crx_id = dict(self.__protobuf_fields(value))[1]

        public_key: bytes = next(k for k in public_keys if sha256(k).digest()[:16] == crx_id)

        extension_path: str = os.path.join(target_dir, Path(crx_path).stem)

        if os.path.exists(extension_path):
            rmtree(extension_path)

        with ZipFile(crx_path, "r") as z:
            z.extractall(extension_path)

        manifest_path: str = os.path.join(extension_path, "manifest.json")

        with open(manifest_path, "r", encoding="utf-8-sig") as f:
            manifest: dict = json.load(f)

        manifest["key"] = b64encode(public_key).decode()

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.debug(f"{Path(crx_path).name} unpacked to {extension_path}")

        return extension_path

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
