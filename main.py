from sys import argv
from os import getenv
from typing import Union
from bridge import Bridge
from toolbox.chrome import Chrome
from toolbox.logger import logger
from toolbox.recorder import ScreenRecorder
from toolbox.utils import retry, ETERNL_NETWORKS, METAMASK_NETWORKS
from wallets.eternl import Eternl
from wallets.metamask import MetaMask


def init_wallet(
        driver: Chrome,
        subnetwork: str,
        need_unlock: bool,
        token_name: str = "unknown"
) -> Union[Eternl, MetaMask]:

    logger.debug(f"Initializing {subnetwork} wallet")

    sn: str = subnetwork.lower()

    if sn in ETERNL_NETWORKS:

        network, connect = ETERNL_NETWORKS[sn]

        wallet = Eternl(
            driver=driver,
            network=network,
            subnetwork=subnetwork,
            token_name=token_name,
            connect=connect
        )

    elif sn in METAMASK_NETWORKS:

        wallet = MetaMask(
            driver=driver,
            subnetwork=subnetwork,
            token_name=token_name,
            need_unlock=need_unlock
        )

    else:

        raise Exception(f"Not supported chain {subnetwork}")

    logger.debug(f"{subnetwork} wallet initialized successfully")

    return wallet


@retry(tries=5)
def main(
        bridge_name: str,
        source_subnetwork: str,
        source_token: str,
        destination_subnetwork: str,
        amount: str
) -> None:

    chrome = Chrome()
    screen_recorder = ScreenRecorder(driver=chrome)
    screen_recorder.start_recording()

    try:

        src_wlt: Union[Eternl, MetaMask] = init_wallet(
            driver=chrome,
            subnetwork=source_subnetwork,
            need_unlock=True,
            token_name=source_token
        )

        dest_wlt: Union[Eternl, MetaMask] = init_wallet(
            driver=chrome,
            subnetwork=destination_subnetwork,
            need_unlock=False if type(src_wlt) is MetaMask else True
        )

        bridge = Bridge(
            driver=chrome,
            bridge_name=bridge_name,
            source_wallet=src_wlt,
            destination_wallet=dest_wlt
        )

        bridge.bridging(amount=amount)

    finally:

        screen_recorder.stop_recording()
        chrome.quit()


if __name__ == '__main__':
    try:

        logger.info("*" * 45)
        logger.info(f"{argv[1]} Bridge")
        logger.info(f"{getenv('BRIDGE_URL')}")
        logger.info(f"Source chain: {argv[2]}")
        logger.info(f"Destination chain: {argv[5]}")
        logger.info("*" * 45)

        main(
            bridge_name=argv[1],
            source_subnetwork=argv[2],
            source_token=argv[4],
            destination_subnetwork=argv[5],
            amount=argv[3]
        )

    except Exception as error:
        # if recovery from the error is not possible
        logger.critical(error, exc_info=True)
