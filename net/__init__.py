import os
import threading
import select
import queue
import time
import logging

logger = logging.getLogger(__name__)


class Loop:
    def __init__(self, sock):
        self.interrupted = threading.Event()
        self.pipe = os.pipe()
        self.sock = sock
        self.thread = threading.Thread(target=self.__loop, name="NetworkLoop")
        self.queue = queue.Queue()

    def __loop(self):
        while not self.interrupted.is_set():
            rlist, wlist, xlist = select.select(
                self.__build_rlist(), self.__build_wlist(), self.__build_xlist()
            )
            if self.interrupted.is_set():
                break

            self.__process_rlist(rlist)
            self.__process_wlist(wlist)
            self.__process_xlist(xlist)

    def __build_rlist(self):
        return [self.sock, self.pipe[0]]

    def __build_wlist(self):
        if self.queue.empty():
            return []
        return [self.sock]

    def __build_xlist(self):
        return self.__build_rlist() + self.__build_wlist()

    def __process_rlist(self, rlist):
        for fd in rlist:
            if fd == self.sock:
                data, addr = self.sock.recvfrom(1024)  # TODO
                logging.info(f"Received {len(data)} from {addr}")
            elif fd == self.pipe[0]:
                os.read(self.pipe[0], 1)

    def __process_wlist(self, wlist):
        for fd in wlist:
            if fd == self.sock:
                try:
                    data = self.queue.get_nowait()
                except queue.Empty:
                    continue
                logging.info("Sending TODO")
                self.sock.sendto(data, ("127.0.0.1", 2000))  # TODO
        # TODO

    def __process_xlist(self, xlist):
        pass
        # TODO

    def start(self):
        self.thread.start()

    def stop(self):
        self.interrupted.set()
        os.write(self.pipe[1], b"x")  # TODO extract
        self.thread.join()

    def send(self, data):
        self.queue.put(data)
        os.write(self.pipe[1], b"w")  # TODO extract
