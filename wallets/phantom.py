import json
from os import getenv
from time import sleep
from requests import get
from typing import Union
from websocket import WebSocket, create_connection
from toolbox.chrome import Chrome
from toolbox.logger import logger
from toolbox.utils import retry, get_receive_address


class Phantom:
    def __init__(
            self,
            driver: Chrome,
            subnetwork: str,
            token_name: str,
            need_unlock: bool
    ) -> None:

        self.__extension_url: str = "chrome-extension://bfnaelmomeimhlpmgjnjophhpkkoljpa"        
        self.__notification_url: str = f"{self.__extension_url}/notification.html"
        self.__driver: Chrome = driver
        self.__sign_key: str = getenv('SIGN_KEY')
        self.__subnetwork: str = subnetwork
        self.__token_name: str = token_name
        self.__receive_address: str = ""
        self.__need_unlock: bool = need_unlock # actually not used, but kept for consistency with other wallets

        self.__set_receive_address_from_env()

    def __set_receive_address_from_env(self) -> None:

        self.__receive_address = get_receive_address(self.__subnetwork)
        logger.info(f"{self.__subnetwork} address: {self.__receive_address}")

    def __find_popup_target(self) -> Union[dict, None]:

        debugger_address: str = self.__driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        targets: dict = get(f"http://{debugger_address}/json").json()

        for target in targets:

            if target.get("type") == "page" and target.get("url", "") == self.__notification_url:
                return target

        return None

    @staticmethod
    def __cdp_evaluate(web_socket: WebSocket, call_id: int, expression: str) -> str:

        web_socket.send(json.dumps({
            "id": call_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True
            }
        }))

        while True:

            message = json.loads(web_socket.recv())

            if message.get("id") == call_id:
                return message.get("result", {}).get("result", {}).get("value")

    @retry()
    def sign_and_confirm_transaction(self) -> None:
        logger.debug("Waiting for Phantom popup to open")

        for _ in range(30):

            target = self.__find_popup_target()

            if target:
                break

            sleep(1)

        else:
            logger.critical("Phantom popup did not open")
            raise ValueError

        logger.debug(f"Phantom popup found: {target['id']}")

        # The Phantom popup is opened by the extension itself (not by this driver's session),
        # so it never shows up in driver.window_handles and switch_to.window() cannot reach it,
        # so we talk to it directly over its own CDP connection instead.
        web_socket: WebSocket = create_connection(target["webSocketDebuggerUrl"])
        call_id: int = 0

        try:

            sleep(3)

            logger.debug("Unlocking Phantom wallet")

            call_id += 1
            self.__cdp_evaluate(
                web_socket,
                call_id,
                f"""
                (function() {{
                    const el = document.evaluate(
                        '//*[@id="unlock-form"]/div/div/input',
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    ).singleNodeValue;

                    if (!el) return false;

                    const val = {json.dumps(self.__sign_key)};
                    const lastValue = el.value;
                    el.value = val;
                    const tracker = el._valueTracker;

                    if (tracker) {{
                        tracker.setValue(lastValue);
                    }}

                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }})();
                """
            )

            call_id += 1
            self.__cdp_evaluate(
                web_socket,
                call_id,
                """
                (function() {
                    const el = document.evaluate(
                        '//*[@id="root"]/div[1]/div/div/div[2]/div/div/button',
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    ).singleNodeValue;

                    if (!el) return false;

                    el.click();
                    return true;
                })();
                """
            )

            logger.debug("Phantom unlocked successfully")

            sleep(3)

            logger.debug("Confirming the transaction")

            call_id += 1
            self.__cdp_evaluate(
                web_socket,
                call_id,
                """
                (async function() {
                    function byXpath(xpath) {
                        return document.evaluate(
                            xpath,
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        ).singleNodeValue;
                    }

                    const primary = byXpath('//*[@id="root"]/div[1]/div[1]/div/div[2]/button[2]');

                    if (primary) {
                        primary.click();
                        return true;
                    }

                    const fallbackButton = byXpath('//*[@id="root"]/div[1]/div[1]/div/div[2]/div/button');

                    if (!fallbackButton) return false;

                    fallbackButton.click();

                    await new Promise(resolve => setTimeout(resolve, 3000));

                    const fallbackInput = byXpath('//*[@id="root"]/div[1]/div[1]/div/div[2]/button');

                    if (!fallbackInput) return false;

                    fallbackInput.click();

                    await new Promise(resolve => setTimeout(resolve, 3000));

                    const finalButton = byXpath('//*[@id="root"]/div[1]/div[1]/div/div[2]/div[2]/p');

                    if (!finalButton) return false;

                    finalButton.click();
                    return true;
                })();
                """
            )

            # wait for the transaction to be confirmed
            sleep(5)

            logger.debug("The transaction confirmation done successfully")

        finally:

            web_socket.close()

    def get_receive_address(self) -> str:

        return self.__receive_address

    def get_subnetwork(self) -> str:

        return self.__subnetwork

    def get_web_app_identifier(self) -> str:

        return self.__subnetwork

    def get_token_name(self) -> str:

        return self.__token_name
