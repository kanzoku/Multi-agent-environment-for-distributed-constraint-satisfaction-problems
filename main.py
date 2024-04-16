import multiprocessing
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
        self.task_queue = connections[self.name]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = sorted(all_domains)  # Liste aller möglicher eigener Domains
        self.nogood_dict = dict()  # Dictionary mit No-goods Key: Constraint-String Value: Liste von no-good Domains
        self.agent_view = dict()  # Dictionary mit den Domains, die der Agent betrachtet
        self.running = True

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
        print(message)
        #self.log_queue.put(f"Agent {self.agent_id} ({self.name}) - {message}")

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = json.dumps({"header": header, "message": message})
        recipient_queue.put((self.name, message_data))

    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            print(f"Received unknown message type: {header} with message: {message}")
            #self.log(f"Received unknown message type: {header} with message: {message}")

    def nogood(self, constraintDict):
        # Aktualisiert das Dictionary der No-goods und probiert die Constraints mit einer neuen Domain
        # zu erfüllen ansonsten wird eine "nogood"-Nachricht an den vorherigen Agenten gesendet
        #self.log(f"Received nogood from {constraintDict['identifier']}")
        old_identifier = self.remove_last(constraintDict["identifier"])
        if old_identifier not in self.nogood_dict:
            self.nogood_dict[old_identifier] = []
        self.nogood_dict[old_identifier].append(constraintDict[self.name])
        self.agent_view[old_identifier].remove(constraintDict[self.name])
        if len(self.agent_view[old_identifier]) == 0:
            constraintDict["identifier"] = old_identifier
            constraintDict.pop(self.name, None)
            self.send_message(self.connections[self.last_sender(constraintDict)],
                              "nogood", constraintDict)
        else:
            constraintDict["identifier"] = (old_identifier +
                                            f";{self.name}={self.agent_view[constraintDict['identifier']][0]}")
            constraintDict[self.name] = self.agent_view[old_identifier][0]
            for constraint in self.constraints:
                if constraint not in constraintDict:
                    self.send_message(self.connections[constraint], "check", constraintDict)

    def check(self, constraintDict):
        # Überprüft, ob es eine Möglichkeit gibt die Constraints zu erfüllen mit
        # den aktuellen Domains-String und fragt die anderen nicht im Domain-String
        # enthaltenen Agenten, ob die Auswahl gültig ist
        if constraintDict["identifier"] not in self.agent_view:
            self.agent_view[constraintDict["identifier"]] = []
            self.solve(constraintDict)
            if len(self.agent_view[constraintDict["identifier"]]) == 0:
                constraintDict.pop(self.name, None)
                self.send_message(self.connections[self.last_sender(constraintDict)]
                                  , "nogood", constraintDict)
                pass
        constraintDict["identifier"] = (constraintDict["identifier"] +
                                        f";{self.name}={self.agent_view[constraintDict['identifier']][0]}")
        constraintDict[self.name] = self.agent_view[constraintDict["identifier"]][0]

        i = 0
        for constraint in self.constraints:
            if constraint not in constraintDict:
                self.send_message(self.connections[constraint], "check", constraintDict)
                i += 1
        if i == 0:
            print(f"Found solution: {constraintDict}")

    def stop(self, message):
        # Beendet den Agenten
        #self.log("Received kill message.")
        #self.log("Stopping agent.")
        #self.join()
        self.running = False
        print(f"Agent {self.agent_id} ({self.name}) stopped.")

    def startagent(self, message):
        # Startet den Agenten
        #self.log("Received start message.")
        #self.log("Starting agent.")
        self.check(constraintDict={"identifier": self.name})

    def solve(self, constraintDict):
        # Löst alle Constraints mit den gegebenen Domains und findet valide Lösungsmenge
        unique_values = set()
        for constraint in constraintDict:
            if self.constraints.contains(constraint):
                unique_values.add(constraintDict[constraint])
        for domain in self.all_domains:
            if domain not in unique_values:
                self.agent_view[constraintDict["identifier"]].append(domain)
        #self.log(f"Found domains: {self.agent_view} for {constraintDict['identifier']}")

    def run(self):
        # Hauptloop des Agenten, um Nachrichten zu empfangen und verarbeiten
        while self.running:
            sender, message_data = self.task_queue.get()  # Warten auf eine neue Nachricht
            message_dict = json.loads(message_data)
            header = message_dict["header"]
            message = message_dict["message"]
            #self.log(f"Received message from agent {sender}: {message_data}")
            self.receive_message(header, message)


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    setup_logger()
    log_queue = Queue()
    # TODO Initialisierung der Agenten und des Sodoku-Problems und Start-Message an den ersten Agenten senden
    with Manager() as manager:
        n = 4
        all_domain_list = list(range(1, n + 1))
        problem = Sudoku_Problem(n, n_ary=False, conflict=False)
        #print(problem.constraints)
        constraint_dict = {}
        for constraint, variables in problem.constraints:
            for var in variables:
                if var not in constraint_dict:
                    constraint_dict[var] = {}
            # Fügen Sie alle verbundenen Variablen und ihre entsprechenden Constraints hinzu
                for connected_var in variables:
                    if connected_var != var:
                        constraint_dict[var][connected_var] = constraint
        connections = dict()
        for cell in problem.cells:
            for variable in cell:
                connections[variable] = manager.Queue()
        agents = []
        i = 0
        for cell in problem.cells:
            for variable in cell:
                agent = AttributAgent(agent_id=i, log_queue=log_queue, name=variable,
                                  connections=connections, constraints=constraint_dict[variable],
                                  all_domains=all_domain_list)
                agents.append(agent)
                i += 1
                #agent.start()

        for agent in agents:
            agent.start()
        print("Schlafe nun")
        time.sleep(1)
        print("Wach auf")
        for agent in agents:
            agent.send_message(agent.task_queue, "kill", {"kill": ""})
        print("Schlafe nun")
        time.sleep(1)
        print("Wach auf")
        log_queue.close()
        for agent in agents:
            agent.join()

