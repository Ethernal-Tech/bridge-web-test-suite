from time import sleep
from functools import wraps
from dataclasses import dataclass


@dataclass(frozen=True)
class Network:
    apex: str = 'apex'
    cardano: str = 'cardano'


@dataclass(frozen=True)
class EternlApexFusionIdentifier:
    prime_testnet: str = 'afpt'
    vector_testnet: str = 'afvt'


@dataclass(frozen=True)
class ApexFusionSubnetwork:
    prime: str = 'prime'
    vector: str = 'vector'
    nexus: str = 'nexus'


@dataclass(frozen=True)
class EternlCardanoIdentifier:
    preview: str = 'preview'


@dataclass(frozen=True)
class CardanoSubnetwork:
    preview: str = 'preview'


def retry(tries: int = 10, delay: int = 1, back_off: float = 1.5):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            f_tries, f_delay = tries, delay
            while f_tries > 0:
                try:
                    return f(*args, **kwargs)
                except Exception:
                    sleep(f_delay)
                    f_tries -= 1
                    f_delay *= back_off
            return f(*args, **kwargs)
        return f_retry
    return deco_retry
