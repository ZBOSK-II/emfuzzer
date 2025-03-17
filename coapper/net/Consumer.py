from typing import Protocol

from .Address import Address


class Consumer(Protocol):

    def on_received(self, addr: Address, data: bytes) -> None:
        pass

    def on_sent(self, addr: Address, data: bytes) -> None:
        pass
