from sys import argv
from os import getenv
from typing import Union
from datetime import datetime
from bridge import Bridge
from toolbox.chrome import Chrome
from toolbox.utils import Network, retry
from toolbox.utils import EternlApexFusionIdentifier, ApexFusionSubnetwork
from toolbox.utils import EternlCardanoIdentifier, CardanoSubnetwork
from wallets.eternl import Eternl
from wallets.metamask import MetaMask


def recover_wallet(
        driver: Chrome,
        token_name: str,
        subnetwork: str
) -> Union[Eternl, MetaMask, None]:

    if subnetwork == ApexFusionSubnetwork.prime:

        wallet = Eternl(
            driver=driver,
            network=Network.apex,
            subnetwork=ApexFusionSubnetwork.prime,
            token_name=token_name,
            connect=EternlApexFusionIdentifier.prime_testnet,
            sign_key=getenv('SIGN_KEY'),
            extension=getenv('ETERNL_WALLET_EXTENSION')
        )

        wallet.recover(
            recovery_phrase=getenv('PRIME_WALLET_RECOVERY_PHRASE')
        )

    elif subnetwork == ApexFusionSubnetwork.vector:

        wallet = Eternl(
            driver=driver,
            network=Network.apex,
            subnetwork=ApexFusionSubnetwork.vector,
            token_name=token_name,
            connect=EternlApexFusionIdentifier.vector_testnet,
            sign_key=getenv('SIGN_KEY'),
            extension=getenv('ETERNL_WALLET_EXTENSION')
        )

        wallet.recover(
            recovery_phrase=getenv('VECTOR_WALLET_RECOVERY_PHRASE')
        )

    elif subnetwork == ApexFusionSubnetwork.nexus:

        wallet = MetaMask(
            driver=driver,
            sign_key=getenv('SIGN_KEY'),
            subnetwork=ApexFusionSubnetwork.nexus,
            token_name=token_name
        )

        wallet.recover(
            recovery_phrase=getenv('NEXUS_WALLET_RECOVERY_PHRASE')
        )

        wallet.add_network(
            name=getenv('NEXUS_NETWORK_NAME'),
            rpc_url=getenv('NEXUS_NETWORK_RPC_URL'),
            chain_id=getenv('NEXUS_NETWORK_CHAIN_ID'),
            currency_symbol=getenv('NEXUS_NETWORK_CURRENCY_SYMBOL')
        )

    elif subnetwork == CardanoSubnetwork.preview:

        wallet = Eternl(
            driver=driver,
            network=Network.cardano,
            subnetwork=CardanoSubnetwork.preview,
            token_name=token_name,
            connect=EternlCardanoIdentifier.preview,
            sign_key=getenv('SIGN_KEY'),
            extension=getenv('ETERNL_WALLET_EXTENSION')
        )

        wallet.recover(
            recovery_phrase=getenv('PREVIEW_WALLET_RECOVERY_PHRASE')
        )

    else:
        return None

    return wallet


@retry(tries=5)
def main(
        bridge_name: str,
        deployment: str,
        source_subnetwork: str,
        source_token: str,
        destination_subnetwork: str,
        destination_token: str,
        amount: str
) -> None:

    chrome = Chrome(
        driver_version=getenv('CHROMEDRIVER_VERSION'),
        eternl_wallet_extension=getenv('ETERNL_WALLET_EXTENSION')
    )

    if bridge_name == 'reactor':

        if deployment == 'internal':
            web_app_url = getenv('INTERNAL_REACTOR_URL')
        elif deployment == 'partner':
            web_app_url = getenv('PARTNER_REACTOR_URL')
        else:
            raise Exception

    elif bridge_name == 'skyline':

        if deployment == 'internal':
            web_app_url = getenv('INTERNAL_SKYLINE_URL')
        else:
            raise Exception

    else:
        raise Exception

    bridge = Bridge(
        driver=chrome,
        bridge_name=bridge_name,
        bridge_url=web_app_url,
        apex_faucet_url=getenv('APEX_FUSION_FAUCET_URL'),
        source_wallet=recover_wallet(
            driver=chrome,
            subnetwork=source_subnetwork,
            token_name=source_token
        ),
        destination_wallet=recover_wallet(
            driver=chrome,
            subnetwork=destination_subnetwork,
            token_name=destination_token
        )
    )

    transaction_signed_error = bridge.bridging(
        amount=amount
    )

    chrome.quit()

    if transaction_signed_error != "":
        raise Exception


if __name__ == '__main__':
    try:

        bdg = argv[1]
        depl = argv[2]

        ss = argv[3]
        amt = argv[4]
        st = argv[5]

        ds = argv[6]
        dt = argv[7]

        print(f"{datetime.now()} Bridge: {bdg} {depl}")
        print(f"{datetime.now()} Transaction: {ss} {amt}{st} to {ds} {amt}{dt}")

        main(
            bridge_name=bdg.lower(),
            deployment=depl.lower(),
            source_subnetwork=ss.lower(),
            source_token=st.lower(),
            destination_subnetwork=ds.lower(),
            destination_token=dt.lower(),
            amount=amt
        )

        print(f"{datetime.now()} Bridging completed")

    except Exception as error:
        # if recovery from the error is not possible
        print(f"{datetime.now()} Bridging failed: {error}")
