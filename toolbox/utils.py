from time import sleep
from functools import wraps
from dataclasses import dataclass
from datetime import datetime


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
            last_exception = None
            while f_tries > 0:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    f_tries -= 1
                    print(f"{datetime.now()} - [{f.__module__}] Retrying '{f.__name__}' due to: {repr(e)}")
                    sleep(f_delay)
                    f_delay *= back_off
            print(f"{datetime.now()} - [{f.__module__}] Function '{f.__name__}' failed after {tries} attempts.")
            raise last_exception
        return f_retry
    return deco_retry
