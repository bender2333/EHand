import os
import termios
import tty
from typing import Optional


class UartPort:
    def __init__(self, port: str = "/dev/ttyUSB1", baud: int = 9600):
        self.port = port
        self.baud = baud
        self.fd: Optional[int] = None
        self._open()

    def _open(self) -> None:
        self.fd = os.open(self.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        baud_const = getattr(termios, f"B{self.baud}", termios.B9600)
        attrs[4] = baud_const
        attrs[5] = baud_const
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

    def write(self, data: bytes) -> int:
        if self.fd is None:
            return 0
        return os.write(self.fd, data)

    def read(self, max_bytes: int = 1024) -> bytes:
        if self.fd is None:
            return b""
        try:
            return os.read(self.fd, max_bytes)
        except BlockingIOError:
            return b""

    def close(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
