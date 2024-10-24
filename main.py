from os import getenv
from toolbox.chrome import Chrome
from toolbox.utils import EternlApexFusionNetwork, ApexFusionChain
from wallets.eternl import Eternl
from wallets.metamask import MetaMask
from apex_fusion_reactor import ApexFusionReactor


if __name__ == '__main__':
    chrome = Chrome()

    nexus_wallet = MetaMask(
        driver=chrome,
        sign_key=getenv('SIGN_KEY')
    )

    nexus_wallet.recover(
        recovery_phrase=getenv('NEXUS_WALLET_RECOVERY_PHRASE')
    )

    nexus_wallet.add_network(
        name=getenv('NEXUS_NETWORK_NAME'),
        rpc_url=getenv('NEXUS_NETWORK_RPC_URL'),
        chain_id=getenv('NEXUS_NETWORK_CHAIN_ID'),
        currency_symbol=getenv('NEXUS_NETWORK_CURRENCY_SYMBOL')
    )

    prime_wallet = Eternl(
        driver=chrome,
        network=EternlApexFusionNetwork.prime_testnet,
        sign_key=getenv('SIGN_KEY'),
        name='Prime'
    )

    prime_wallet.recover(
        recovery_phrase=getenv('PRIME_WALLET_RECOVERY_PHRASE')
    )

    vector_wallet = Eternl(
        driver=chrome,
        network=EternlApexFusionNetwork.vector_testnet,
        sign_key=getenv('SIGN_KEY'),
        name='Vector'
    )

    vector_wallet.recover(
        recovery_phrase=getenv('VECTOR_WALLET_RECOVERY_PHRASE')
    )

    apex_fusion_reactor = ApexFusionReactor(
        driver=chrome,
        reactor_url=getenv('APEX_FUSION_REACTOR_URL'),
        faucet_url=getenv('APEX_FUSION_FAUCET_URL'),
        prime_wallet=prime_wallet,
        vector_wallet=vector_wallet,
        nexus_wallet=nexus_wallet
    )

    apex_fusion_reactor.bridging(
        source=ApexFusionChain.prime,
        destination=ApexFusionChain.vector,
        amount=getenv('PRIME_TO_VECTOR_AMOUNT')
    )

    apex_fusion_reactor.bridging(
        source=ApexFusionChain.prime,
        destination=ApexFusionChain.nexus,
        amount=getenv('PRIME_TO_NEXUS_AMOUNT')
    )

    apex_fusion_reactor.bridging(
        source=ApexFusionChain.vector,
        destination=ApexFusionChain.prime,
        amount=getenv('VECTOR_TO_PRIME_AMOUNT')
    )

    apex_fusion_reactor.bridging(
        source=ApexFusionChain.nexus,
        destination=ApexFusionChain.prime,
        amount=getenv('NEXUS_TO_PRIME_AMOUNT')
    )

    chrome.quit()
