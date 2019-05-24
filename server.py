import sys
import threading
import select
import configuration as conf
from CommunicationHandler import CommunicationHandler
from Networking import OutConnection, InConnection, Connection
from enum import Enum
import argparse
import logging
import json

TIMEOUT = 60


class Machine(Enum):
    HOST = 0,
    VM = 1


class NetworkCommunicator(threading.Thread):

    def __init__(self, machine_type):
        threading.Thread.__init__(self)
        self.bind_ip = None
        self.machine_type = machine_type

        self._watchtower_line = None
        self._command_line = None
        self.Vms = list()

        if self.machine_type == Machine.HOST:
            self.bind_ip = conf.HOST_IP
        else:
            self.bind_ip = conf.VM_IP

        self.start()

    def _initConnections(self):
        try:
            self._watchtower_line = InConnection(self.bind_ip, conf.BIND_PORT)
            self._command_line = InConnection("127.0.0.1", conf.BIND_PORT)
        except OSError:
            logging.error("[x] Fail to create watchtowers.")
            return 1
        return 0

    def run(self):
        global TIMEOUT

        logging.info("[i] Starting wachtowers...")
        if self._initConnections() == -1:
            return -1

        time_counter = 0
        connections = [self._watchtower_line, self._command_line]
        sockets = [c.GetSocket() for c in connections]
        while time_counter < TIMEOUT:
            time_counter += 1
            rr, rw, err = select.select(sockets,
                                        [], [], 1.0)
            if len(rr) == 0 and len(rw) == 0 and len(err) == 0:
                continue

            for sock in rr:
                logging.debug(f"[ ] Incomming connection. {sock}")
                (new_sock, address) = sock.accept()
                new_conn = Connection(address, "", new_sock)
                self.Vms.append(address)
                _ = CommunicationHandler(new_conn)

        self._watchtower_line.Close()
        self._command_line.Close()
        logging.info(f"[i] End the watch.")
        return 0


def _set_logging(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    logging.basicConfig(format="%(message)s", level=numeric_level)


def _parse_agrs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log",
                        help="log level that sould be logged on screen" +
                             " (default INFO)",
                        default="INFO",
                        choices=["DEBUG", "INFO", "WARN", "ERROR"])
    subparsers = parser.add_subparsers()

    save_parser = subparsers.add_parser("host")
    save_parser.set_defaults(**{"machine": Machine.HOST})

    label_parser = subparsers.add_parser("vm")
    label_parser.set_defaults(**{"machine": Machine.VM})

    args = parser.parse_args()
    return args


def main():
    args = _parse_agrs()
    print(args)
    _set_logging(args.log)
    communication = NetworkCommunicator(args.machine)

    if args.machine == Machine.VM:
        conn = OutConnection(conf.HOST_IP, conf.BIND_PORT)
        pkg = {
            'type': 'hello',
            'ip': conf.VM_IP,
            'port': conf.BIND_PORT
        }
        conn.Send(bytes(json.dumps(pkg), 'utf-8'))

    # wait
    communication.join()
    return 0


sys.exit(main())
