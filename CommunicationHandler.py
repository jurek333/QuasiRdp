from Networking import Connection, OutConnection
import threading
import logging
import json


class CommunicationHandler(threading.Thread):

    def __init__(self, connection: Connection):
        threading.Thread.__init__(self)
        self._connection = connection
        self.start()

    def run(self):
        logging.debug("Start reciving")
        # get the package
        package = self._connection.Recv()
        self._connection.Close()

        if package is not False:
            print("Odebrano:")
            print(package)
            pkg = json.loads(package)
            if pkg["type"] == "hello":
                c = OutConnection(pkg["ip"], pkg["port"])
                resp = {
                    'type': 'ack'
                }
                c.Send(bytes(json.dumps(resp), 'utf-8'))
        else:
            print("\t\t Pobieranie pakiety się nie powiodło...")

        return 0
