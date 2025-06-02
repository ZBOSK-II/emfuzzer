# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
CoAP - Constrained Application Protocol support module.
"""

from enum import StrEnum, auto
from typing import Self

from ..config import Config
from ..context import Context
from ..delay import Delay
from ..injector.subtask import TypedInjectionSubTask
from ..io import IOLoop, SendQueue
from ..io.net import NetworkAddress
from ..io.sockets import UdpClientSocket
from ..subtasks.subtask import SubTask, TypedSubTask
from .validator import Validator


class CoapMonitorResult(StrEnum):
    SUCCESS = auto()
    UNEXPECTED_MESSAGE_RECEIVED = auto()


class CoapMonitor(TypedSubTask[CoapMonitorResult]):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        io: IOLoop,
        target: NetworkAddress,
        response_timeout: float,
        observation_timeout: float,
    ):
        super().__init__(name)
        self._io = io
        self._target = target
        self._response_timeout = response_timeout
        self._delay = Delay(observation_timeout, name + ".observation")

        self._validator: Validator | None = None
        self._socket: UdpClientSocket | None = None
        self._queue: SendQueue[tuple[NetworkAddress, bytes]] | None = None

    def start(self) -> CoapMonitorResult | SubTask.StartedType:
        self._queue = self._io.make_queue(tuple[NetworkAddress, bytes])
        self._validator = Validator(self._target, self._response_timeout)
        self._socket = UdpClientSocket(
            self.name() + ".udp", self._queue, self._validator
        )
        self._io.register(self._socket)
        return SubTask.STARTED

    def finish(self) -> CoapMonitorResult:
        assert self._socket
        assert self._validator
        self._delay.wait()
        self._io.close(self._socket)
        return (
            CoapMonitorResult.SUCCESS
            if self._validator.unexpected_messages == 0
            else CoapMonitorResult.UNEXPECTED_MESSAGE_RECEIVED
        )

    def result_type(self) -> type[CoapMonitorResult]:
        return CoapMonitorResult

    def send(self, data: bytes) -> None:
        assert self._queue is not None
        self._queue.put((self._target, data))

    def wait_for_response(self) -> Validator.Result:
        assert self._validator
        return self._validator.wait_for_result()

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        result = cls(
            name=name,
            target=NetworkAddress.from_config(config.section("target")),
            response_timeout=config.get_float("response_timeout"),
            observation_timeout=config.get_float("observation_timeout"),
            io=context.worker(IOLoop),
        )
        context.register_data(name, result)
        return result


class CoapInjector(TypedInjectionSubTask[Validator.Result]):
    def __init__(self, name: str, monitor: CoapMonitor):
        super().__init__(name)
        self._monitor = monitor

    def inject(self, data: bytes) -> Validator.Result:
        self._monitor.send(data)
        return self._monitor.wait_for_response()

    def result_type(self) -> type[Validator.Result]:
        return Validator.Result

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            monitor=context.data(CoapMonitor, config.get_str("monitor")),
        )
