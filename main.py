from sys import argv
from os import getenv
from typing import Union
from toolbox.chrome import Chrome
from toolbox.utils import EternlApexFusionNetwork, ApexFusionChain, retry
from wallets.eternl import Eternl
from wallets.metamask import MetaMask
from apex_fusion_reactor import ApexFusionReactor


@retry()
def recover_wallet(
        driver: Chrome,
        target: str
) -> Union[Eternl, MetaMask, None]:

    if target == ApexFusionChain.prime:

        wallet = Eternl(
            driver=driver,
            network=EternlApexFusionNetwork.prime_testnet,
            sign_key=getenv('SIGN_KEY'),
            name=ApexFusionChain.prime
        )

        wallet.recover(
            recovery_phrase=getenv('PRIME_WALLET_RECOVERY_PHRASE')
        )

    elif target == ApexFusionChain.vector:

        wallet = Eternl(
            driver=driver,
            network=EternlApexFusionNetwork.vector_testnet,
            sign_key=getenv('SIGN_KEY'),
            name=ApexFusionChain.vector
        )

        wallet.recover(
            recovery_phrase=getenv('VECTOR_WALLET_RECOVERY_PHRASE')
        )

    elif target == ApexFusionChain.nexus:

        wallet = MetaMask(
            driver=driver,
            sign_key=getenv('SIGN_KEY'),
            name=ApexFusionChain.nexus
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

    else:
        return None

    return wallet


def main(
        source: str,
        destination: str,
        amount: str
) -> None:

    chrome = Chrome()

    apex_fusion_reactor = ApexFusionReactor(
        driver=chrome,
        reactor_url=getenv('APEX_FUSION_REACTOR_URL'),
        faucet_url=getenv('APEX_FUSION_FAUCET_URL'),
        source_wallet=recover_wallet(
            driver=chrome,
            target=source
        ),
        destination_wallet=recover_wallet(
            driver=chrome,
            target=destination
        )
    )

    apex_fusion_reactor.bridging(
        amount=amount
    )

    chrome.quit()


if __name__ == '__main__':
    main(
        source=argv[1].lower(),
        destination=argv[2].lower(),
        amount=argv[3]
    )
