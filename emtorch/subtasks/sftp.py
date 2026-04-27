# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing SFTP operation as sub-tasks.
"""

import logging
from abc import abstractmethod
from typing import Callable, Self

import paramiko

from ..config import Config
from ..context import CaseContext
from ..ssh import ConnectionConfig
from ..ssh.client import open_ssh
from .subtask import BasicSubTask

logger = logging.getLogger(__name__)


class SftpTask(BasicSubTask):
    def __init__(
        self,
        name: str,
        connection_config: ConnectionConfig,
        local_path: str,
        remote_path: str,
    ):
        super().__init__(name)
        self.connection_config = connection_config
        self.local_path = local_path
        self.remote_path = remote_path
        self._ssh: None | paramiko.SSHClient = None
        self._sftp: None | paramiko.SFTPClient = None

    def basic_start(self, context: CaseContext) -> bool:
        try:
            self._ssh = open_ssh(self.connection_config)
            self._sftp = self._ssh.open_sftp()
            return True
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"Failed to open SSH connection <{self.name()}>: {ex}")
            if self._sftp is not None:
                self._sftp.close()
                if self._ssh is not None:
                    self._ssh.close()
                self._sftp = None
                self._ssh = None
            return False

    @abstractmethod
    def perform_action(self) -> None:
        pass

    def finish(self) -> BasicSubTask.Result:
        assert self._sftp
        assert self._ssh
        try:
            self.perform_action()
            return self.Result.SUCCESS
        except TimeoutError:
            return self.Result.TIMEOUT
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(
                f"Failed while performing SFTP operation <{self.name()}>: {ex}"
            )
            return self.Result.ERROR
        finally:
            self._sftp.close()
            self._ssh.close()

    def create_callback(self, infix: str) -> Callable[[int, int], None]:
        def callback(current: int, total: int) -> None:
            logger.info(
                f"{self.local_path} {infix} {self.remote_path}: {current} of {total} bytes"
            )

        return callback


class SftpUpload(SftpTask):
    def perform_action(self) -> None:
        assert self._sftp
        logger.info(f"SFTP PUT {self.local_path} -> {self.remote_path}")
        self._sftp.put(
            localpath=self.local_path,
            remotepath=self.remote_path,
            callback=self.create_callback("->"),
        )

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            connection_config=ConnectionConfig.from_config(
                config.section("connection")
            ),
            remote_path=config.get_str("remote_path"),
            local_path=config.get_str("local_path"),
        )


class SftpDownload(SftpTask):
    def perform_action(self) -> None:
        assert self._sftp
        logger.info(f"SFTP GET {self.local_path} <- {self.remote_path}")
        self._sftp.get(
            localpath=self.local_path,
            remotepath=self.remote_path,
            callback=self.create_callback("<-"),
        )

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            connection_config=ConnectionConfig.from_config(
                config.section("connection")
            ),
            remote_path=config.get_str("remote_path"),
            local_path=config.get_str("local_path"),
        )
