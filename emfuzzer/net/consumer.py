# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

from typing import Protocol

from .address import Address


class Consumer(Protocol):

    def on_received(self, addr: Address, data: bytes) -> None:
        pass

    def on_sent(self, addr: Address, data: bytes) -> None:
        pass
