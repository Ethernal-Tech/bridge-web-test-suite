from enum import Enum
from time import sleep
from functools import wraps
from toolbox.logger import logger


class Network(str, Enum):
    apex = "apex"
    cardano = "cardano"


class EternlApexFusionIdentifier(str, Enum):
    prime_testnet = "afpt"
    vector_testnet = "afvt"


class ApexFusionSubnetwork(str, Enum):
    prime = "prime"
    vector = "vector"
    nexus = "nexus"


class EternlCardanoIdentifier(str, Enum):
    preview = "preview"


class CardanoSubnetwork(str, Enum):
    preview = "preview"


class EthereumSubnetwork(str, Enum):
    polygon = "polygon"
    ethereum = "ethereum"
    katana = "katana"
    sei = "sei"
    scroll = "scroll"
    unichain = "unichain"


class SolanaSubnetwork(str, Enum):
    solana = "solana"


def retry(tries: int = 10, delay: int = 1, back_off: float = 1.5):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            f_tries, f_delay = tries, delay
            while f_tries > 0:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    f_tries -= 1
                    logger.error(f"Remaining attempt: {f_tries}")
                    logger.error(e, exc_info=True)
                    sleep(f_delay)
                    f_delay *= back_off
            logger.critical(f"{f.__name__} failed after {tries} attempts")
            return f(*args, **kwargs)
        return f_retry
    return deco_retry


ETERNL_NETWORKS: dict[str, tuple[str, str]] = {
    ApexFusionSubnetwork.prime: (Network.apex, EternlApexFusionIdentifier.prime_testnet),
    ApexFusionSubnetwork.vector: (Network.apex, EternlApexFusionIdentifier.vector_testnet),
    CardanoSubnetwork.preview: (Network.cardano, EternlCardanoIdentifier.preview),
}


METAMASK_NETWORKS: set[str] = {
    ApexFusionSubnetwork.nexus,
    EthereumSubnetwork.polygon,
    EthereumSubnetwork.ethereum,
    EthereumSubnetwork.katana,
    EthereumSubnetwork.sei,
    EthereumSubnetwork.scroll,
    EthereumSubnetwork.unichain,
}
