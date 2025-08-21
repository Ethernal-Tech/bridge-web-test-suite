from sys import argv
from os import getenv
from typing import Union
from bridge import Bridge
from toolbox.chrome import Chrome
from toolbox.logger import logger
from toolbox.utils import Network, retry
from toolbox.utils import EternlApexFusionIdentifier, ApexFusionSubnetwork
from toolbox.utils import EternlCardanoIdentifier, CardanoSubnetwork
from wallets.eternl import Eternl
from wallets.metamask import MetaMask


def init_wallet(
        driver: Chrome,
        subnetwork: str,
        token_name: str = "unknown"
) -> Union[Eternl, MetaMask]:

    logger.debug(f"Initializing {subnetwork.capitalize()} wallet")

    if subnetwork == ApexFusionSubnetwork.prime:

        wallet = Eternl(
            driver=driver,
            network=Network.apex,
            subnetwork=ApexFusionSubnetwork.prime,
            token_name=token_name,
            connect=EternlApexFusionIdentifier.prime_testnet,
            sign_key=getenv('SIGN_KEY'),
        )

    elif subnetwork == ApexFusionSubnetwork.vector:

        wallet = Eternl(
            driver=driver,
            network=Network.apex,
            subnetwork=ApexFusionSubnetwork.vector,
            token_name=token_name,
            connect=EternlApexFusionIdentifier.vector_testnet,
            sign_key=getenv('SIGN_KEY'),
        )

    elif subnetwork == CardanoSubnetwork.preview:

        wallet = Eternl(
            driver=driver,
            network=Network.cardano,
            subnetwork=CardanoSubnetwork.preview,
            token_name=token_name,
            connect=EternlCardanoIdentifier.preview,
            sign_key=getenv('SIGN_KEY'),
        )

    elif subnetwork == ApexFusionSubnetwork.nexus:

        wallet = MetaMask(
            driver=driver,
            sign_key=getenv('SIGN_KEY'),
            subnetwork=ApexFusionSubnetwork.nexus,
            token_name=token_name
        )

    else:

        raise Exception(f"Not supported chain {subnetwork.capitalize()}")

    logger.debug(f"{subnetwork.capitalize()} wallet initialized successfully")

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

    bridge = Bridge(
        driver=chrome,
        bridge_name=bridge_name,
        source_wallet=init_wallet(
            driver=chrome,
            subnetwork=source_subnetwork,
            token_name=source_token
        ),
        destination_wallet=init_wallet(
            driver=chrome,
            subnetwork=destination_subnetwork
        )
    )

    bridge.bridging(amount=amount)

    chrome.quit()


if __name__ == '__main__':
    try:

        bdg = argv[1]

        ss = argv[2]
        amt = argv[3]
        st = argv[4]

        ds = argv[5]

        logger.info("*" * 45)
        logger.info(f"{bdg.capitalize()} Bridge")
        logger.info(f"{getenv('BRIDGE_URL')}")
        logger.info(f"Source chain: {ss.capitalize()}")
        logger.info(f"Destination chain: {ds.capitalize()}")
        logger.info("*" * 45)

        main(
            bridge_name=bdg.lower(),
            source_subnetwork=ss.lower(),
            source_token=st.lower(),
            destination_subnetwork=ds.lower(),
            amount=amt
        )

    except Exception as error:
        # if recovery from the error is not possible
        logger.critical(error, exc_info=True)
