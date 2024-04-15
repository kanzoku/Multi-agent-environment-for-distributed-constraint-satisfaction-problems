from multiprocessing import Process, Queue, Manager
from loguru import logger
from sudoku_problem import Sudoku_Problem
import time
import json


def setup_logger():
    config = {
        "handlers": [
            {"sink": "file.log", "enqueue": True, "level": "INFO"},
        ],
    }
    logger.configure(**config)


class AttributAgent(Process):
    def __init__(self, agent_id, log_queue, name, connections, constraints, all_domains):
        super(AttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten
        self.name = name  # Name des Agenten
        self.log_queue = log_queue  # Queue für Log-Nachrichten
        self.task_queue = Queue()  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = all_domains  # Liste aller möglicher eigener Domains
        self.nogood_dict = dict()  # Dictionary mit No-goods Key: Constraint-String Value: Liste von no-good Domains
        self.agent_view = dict()  # Dictionary mit den Domains, die der Agent betrachtet

        self.message_handlers = {
            "check": self.check,
            "nogood": self.nogood,
            "kill": self.stop,
            "startagent": self.start
        }

    def last_sender(self, constraintDict):
        # Gibt den Namen des vorherigen Agenten zurück
        return list(constraintDict.keys())[-1]

    def remove_last(self, identifier):
        # Entfernt den letzten Agenten aus dem Constraint-Identifier
        return identifier[:identifier.rfind(";")]
    
    def log(self, message):
        # Sendet Log-Nachrichten an die Log-Queue
        self.log_queue.put(f"Agent {self.agent_id} ({self.name}) - {message}")

    def send_message(self, recipient_queue, message):
        # Sendet Nachrichten an andere Agenten
        recipient_queue.put((self.name, message))

    def receive_message(self, message_data):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        header, message = message_data
        handler = self.message_handlers.get(header)
        if handler:
            constraintDict = json.loads(message) # Lade die Constraints aus der Nachricht als Dictionary
            handler(constraintDict)  # Rufe die zugehörige Funktion auf
        else:
            self.log(f"Received unknown message type: {header} with message: {message}")

    def nogood(self, constraintDict):
        # Aktualisiert das Dictionary der No-goods und probiert die Constraints mit einer neuen Domain
        # zu erfüllen ansonsten wird eine "nogood"-Nachricht an den vorherigen Agenten gesendet
        self.log(f"Received nogood from {constraintDict['identifier']}")
        old_identifier = self.remove_last(constraintDict["identifier"])
        if old_identifier not in self.nogood_dict:
            self.nogood_dict[old_identifier] = []
        self.nogood_dict[old_identifier].append(constraintDict[self.name])
        self.agent_view[old_identifier].remove(0)
        if len(self.agent_view[old_identifier]) == 0:
            constraintDict["identifier"] = old_identifier
            constraintDict.pop(self.name, None)
            self.send_message(self.connections[self.last_sender(constraintDict)],
                              json.dumps({"nogood": constraintDict}))
        else:
            constraintDict["identifier"] = (constraintDict["identifier"] +
                                            f";{self.name}={self.agent_view[constraintDict['identifier']][0]}")
            constraintDict[self.name] = self.agent_view[old_identifier][0]
            self.check(constraintDict)
            for constraint in self.constraints:
                if constraint not in constraintDict:
                    self.send_message(self.connections[constraint], json.dumps({"check": constraintDict}))


    def check(self, constraintDict):
        # Überprüft, ob es eine Möglichkeit gibt die Constraints zu erfüllen mit
        # den aktuellen Domains-String und fragt die anderen nicht im Domain-String
        # enthaltenen Agenten, ob die Auswahl gültig ist
        if constraintDict["identifier"] not in self.agent_view:
            self.agent_view[constraintDict["identifier"]] = []
            self.solve(constraintDict)
            if len(self.agent_view[constraintDict["identifier"]]) == 0:
                # TODO Sende nogood an vorherigen Agenten
                constraintDict.pop(self.name, None)
                self.send_message(self.connections[self.last_sender(constraintDict)]
                                  , json.dumps({"nogood": constraintDict}))
                pass
        constraintDict["identifier"] = (constraintDict["identifier"] +
                                        f";{self.name}={self.agent_view[constraintDict['identifier']][0]}")
        constraintDict[self.name] = self.agent_view[constraintDict["identifier"]][0]

        i = 0
        for constraint in self.constraints:
            if constraint not in constraintDict:
                self.send_message(self.connections[constraint], json.dumps({"check": constraintDict}))
                i += 1
        if i == 0:
            self.send_message(self.connections["log"], json.dumps({"ok": constraintDict}))

    def stop(self, message):
        # Beendet den Agenten
        self.log("Received kill message.")
        self.log("Stopping agent.")
        self.task_queue.close()
        self.join()
        self.kill()

    def startagent(self, message):
        # Startet den Agenten
        self.log("Received start message.")
        self.log("Starting agent.")
        self.check(constraintDict={"identifier": self.name})

    def solve(self, constraintDict):
        # Löst alle Constraints mit den gegebenen Domains und findet valide Lösungsmenge
        unique_values = set(constraintDict.values())
        for domain in self.all_domains:
            if domain not in unique_values:
                self.agent_view[constraintDict["identifier"]].append(domain)
        self.log(f"Found domains: {self.agent_view} for {constraintDict['identifier']}")

    def run(self):
        # Hauptloop des Agenten, um Nachrichten zu empfangen und verarbeiten
        while True:
            message = self.task_queue.get()  # Warten auf eine neue Nachricht
            name, msg = message
            self.log(f"Received message from agent {name}: {msg}")
            self.receive_message(msg)


if __name__ == "__main__":
    setup_logger()
    #log_queue = Queue()
    # TODO Initialisierung der Agenten und des Sodoku-Problems und Start-Message an den ersten Agenten senden
    #manager = Manager()
    problem = Sudoku_Problem(4, n_ary=False, conflict=True)
    #print(problem.constraints)
    #print(problem.cells)
    for cell in problem.cells:
        for variable in cell:
            print(variable)
