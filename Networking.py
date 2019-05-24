import socket
import struct
import logging


class Connection:
    def __init__(self, ip, port, sock):
        self._ip = ip
        self._port = port
        self._socket = sock

    def Send(self, message: bytes):
        size = len(message)
        size_pkg = struct.pack("I", size)
        self._socket.send(size_pkg)
        self._socket.send(message)

    def _recvBytes(self, length):
        recv_size = 0
        data = b''
        while recv_size < length:
            remaining = length - recv_size
            if remaining > 0x4000:
                remaining = 0x4000

            now_recv = self._socket.recv(remaining)

            if now_recv == 0:
                return False

            data += now_recv
            recv_size = len(data)

        return data

    def Recv(self):
        data_with_size = self._recvBytes(4)
        if data_with_size is False:
            return False

        package_size = struct.unpack("I", data_with_size)[0]
        print(F"package_size: {package_size}")
        data = self._recvBytes(package_size)
        if data is False:
            return False
        return data

    def Close(self):
        self._socket.close()
        self._socket = None


class OutConnection(Connection):
    def __init__(self, ip, port):
        Connection.__init__(self, ip, port, None)
        self._connect()

    def _connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:

            self._socket.connect((self._ip, self._port))
            logging.debug(f"Connected to {self._ip}:{self._port}")

        except socket.timeout:
            logging.error("Timeout raised during connection on " +
                          f"socket {self._socket}")
            raise


class InConnection(Connection):
    def __init__(self, ip, port):
        Connection.__init__(self, ip, port, None)
        self._createListeningSocket()
        self._connection_handlers = list()

    def _createListeningSocket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._ip, self._port))
        self._socket.listen(5)

    def GetSocket(self):
        return self._socket
