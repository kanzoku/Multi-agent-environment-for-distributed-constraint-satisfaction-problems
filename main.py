import multiprocessing
from multiprocessing import Process, Queue, Manager
from loguru import logger
from sudoku_problem import Sudoku_Problem
import time
import json
from UnitTest import n9_test2_occupation_dict


def setup_logger():
    config = {
        "handlers": [
            {"sink": "file.log", "enqueue": True, "level": "INFO"},
        ],
    }
    logger.configure(**config)


class AttributAgent(Process):
    def __init__(self, agent_id, log_queue, name, connections, constraints, all_domains,
                 occupation, n=4, *args, **kwargs):
        super(AttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten
        self.name = name  # Name des Agenten
        self.log_queue = log_queue  # Queue für Log-Nachrichten
        self.task_queue = connections[self.name]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = self.unit_testing(occupation, all_domains)  # Liste aller möglicher eigener Domains
        self.nogood_dict = dict()  # Dictionary mit No-goods Key: Constraint-String Value: Liste von no-good Domains
        self.agent_view = dict()  # Dictionary mit den Domains, die der Agent betrachtet
        self.occupation = occupation  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen
        self.n = n  # Anzahl der Agenten

        self.message_handlers = {
            "check": self.check,
            "nogood": self.nogood,
            "kill": self.stop,
            "startagent": self.startagent
        }


    def unit_testing(self, occupation, domains):
        # Testet die Constraints mit den gegebenen Domains und eliminiert invalide Domains
        # if occupation[self.name] is not None:
        #     return {occupation[self.name]}
        set_domain = set()
        for key in occupation:
            if occupation[key] is not None:
                set_domain.add(occupation[key])

        list_domain = []
        for domain in domains:
            if domain not in set_domain:
                list_domain.append(domain)
        if len(list_domain) == 0:
            print("No solution found.")
            self.kill_all()
        # print (f"{self.name} meine Domains: {list_domain}")
        return list_domain

    def occupation_dict(self, occupationDict):
        occupated_dict = self.occupation
        for key in occupated_dict:
            if key in occupationDict:
                occupated_dict[key] = occupationDict[key]
        return occupated_dict

    def occupation_hash(self, occupationDict):
        # Gibt den Hash-Wert der Besetzung des Agenten zurück
        occ_dict = self.occupation_dict(occupationDict)
        hash_str = json.dumps(occ_dict)
        # print(f"Hash: {hash(hash_str)}")
        return occ_dict, hash(hash_str)

    def last_sender(self, sender_list):
        # Gibt den Namen des vorherigen Agenten zurück
        if isinstance(sender_list, list):
            return sender_list[-1]
        else:
            print ("Error: last_sender")

    def kill_all(self):
        # Beendet alle Agenten
        for connection in self.connections:
            self.send_message(self.connections[connection], "kill", {"kill": ""})

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

    def nogood(self, communicationDict):
        # Aktualisiert das Dictionary der No-goods und probiert die Constraints mit einer neuen Domain
        # zu erfüllen ansonsten wird eine "nogood"-Nachricht an den vorherigen Agenten gesendet
        #self.log(f"Received nogood from {constraintDict['identifier']}")
        # print(f"{self.name} received nogood {communicationDict['occupation'][self.name]}"
        #       f" with Hash: {communicationDict['identifier'][-1]}")
        old_identifier = communicationDict["identifier"][-1]

        if old_identifier == "start":
            print("No solution found.")
            self.kill_all()
            return


        if communicationDict["occupation"][self.name] in self.agent_view[old_identifier]:
            self.agent_view[old_identifier].discard(communicationDict["occupation"][self.name])

        if communicationDict["occupation"][self.name] not in self.nogood_dict[old_identifier]:
            self.nogood_dict[old_identifier].add(communicationDict["occupation"][self.name])

        # print(f"{self.name} nogood_dict: {self.nogood_dict[old_identifier]} and"
        #       f" agent_view: {self.agent_view[old_identifier]}")

        if len(self.agent_view[old_identifier]) == 0:
            communicationDict["identifier"].pop()
            communicationDict["sender"].pop()
            communicationDict["occupation"][self.name] = None
            self.send_message(self.connections[self.last_sender(communicationDict["sender"])],
                              "nogood", communicationDict)
        else:
            a = 0
            communicationDict["occupation"][self.name] = self.agent_view[old_identifier].pop()
            for key in self.occupation:
                if communicationDict["occupation"][key] is None:
                    self.send_message(self.connections[key], "check", communicationDict)
                    a += 1
                    # print(f"{self.name} is sending other check to {key} and"
                    #       f" Domain: {communicationDict['occupation'][self.name]}")
                    return

    def check(self, communicationDict):
        # Überprüft, ob es eine Möglichkeit gibt die Constraints zu erfüllen mit
        # den aktuellen Domains-String und fragt die anderen nicht im Domain-String
        # enthaltenen Agenten, ob die Auswahl gültig ist
        occ_dict = dict()
        # print(f"{self.name} is checking"
        #       f" from Sender: {communicationDict['sender'][-1]}")
        if communicationDict["identifier"][-1] == "start":
            hash_identifier = hash("start")
            occ_dict = self.occupation
        else:
            occ_dict, hash_identifier = self.occupation_hash(communicationDict["occupation"])

        if hash_identifier not in self.agent_view and hash_identifier not in self.nogood_dict:
            solve_list = self.solve(communicationDict["occupation"])
            # print(f"{self.name} is solving with Hash: {hash_identifier} and List: {solve_list}")
            if len(solve_list) == 0:
                l_sender = self.last_sender(communicationDict["sender"])
                if l_sender == "start":
                    print("No solution found.")
                    self.kill_all()
                    return
                self.send_message(self.connections[l_sender], "nogood", communicationDict)
                return
            else:
                self.agent_view[hash_identifier] = set(solve_list)
                self.nogood_dict[hash_identifier] = set()
        else:
            # print(f"{self.name} is using old Hash: {hash_identifier}")
            self.agent_view[hash_identifier].update(self.nogood_dict[hash_identifier])
            self.nogood_dict[hash_identifier] = set()

        i = 0
        if len(self.agent_view[hash_identifier]) != 0:
            communicationDict["identifier"].append(hash_identifier)
            communicationDict["occupation"][self.name] = self.agent_view[hash_identifier].pop()
            communicationDict["sender"].append(self.name)
            for key in occ_dict:
                if communicationDict["occupation"][key] is None:
                    self.send_message(self.connections[key], "check", communicationDict)
                    # print(f"{self.name} is sending check to {key} with Hash: {hash_identifier} and"
                    #       f" Domain: {communicationDict['occupation'][self.name]} and"
                    #       f" agent_view: {self.agent_view[hash_identifier]}")
                    i += 1
                    return
        else:
            communicationDict["identifier"].pop()
            communicationDict["sender"].pop()
            communicationDict["occupation"][self.name] = None
            self.send_message(self.connections[self.last_sender(communicationDict["sender"])], "nogood", communicationDict)
            return


        if i == 0:
            self.send_random(communicationDict)

    def send_random(self, communicationDict):
        # Sendet eine Nachricht an einen zufälligen nicht gesetzten Agenten
        for agent in communicationDict["occupation"]:
            if communicationDict["occupation"][agent] is None:
                self.send_message(self.connections[agent], "check", communicationDict)
                return
        print(f"{communicationDict['occupation']}")
        self.kill_all()


    def stop(self, message):
        # Beendet den Agenten
        #self.log("Received kill message.")
        #self.log("Stopping agent.")
        #self.join()
        self.running = False
        # print(f"Agent {self.agent_id} ({self.name}) stopped.")

    def startagent(self, communicationDict):
        # Startet den Agenten
        #self.log("Received start message.")
        #self.log("Starting agent.")
        communicationDict["sender"].append("start")
        communicationDict["identifier"].append("start")
        self.check(communicationDict)

    # Löst alle Constraints mit den gegebenen Domains und findet valide Lösungsmenge
    def solve(self, constraintDict):
        # Startbedingung für den Agenten
        # if len(constraintDict["identifier"]) == 1:
        #     return self.all_domains

        unique_values = set()
        # Findet alle belegten Domains durch Constraints
        for key in self.occupation:
            if key in constraintDict and constraintDict[key] is not None:
                unique_values.add(constraintDict[key])
        # Findet alle möglichen Domains, die noch nicht belegt sind
        list_domains = []
        for domain in self.all_domains:
            if domain not in unique_values:
                list_domains.append(domain)
        return list_domains

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
        n = 9
        all_domain_list = list(range(1, n + 1))
        problem = Sudoku_Problem(n, n_ary=False, conflict=False)
        #print(problem.constraints)
        constraint_dict = {}
        con_dict = {}
        occupation_dict = {}
        for constraint, variables in problem.constraints:
            for var in variables:
                if var not in constraint_dict:
                    constraint_dict[var] = {}
                    con_dict[var] = {}
                    occupation_dict[var] = None
                for connected_var in variables:
                    if connected_var != var:
                        constraint_dict[var][connected_var] = constraint
                        con_dict[var][connected_var] = None

        # import pprint

        occupation_dict = n9_test2_occupation_dict(occupation_dict)

        for key in con_dict:
            for key2 in con_dict[key]:
                if key2 in occupation_dict and not occupation_dict[key2] is None:
                    con_dict[key][key2] = occupation_dict[key2]
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(con_dict)
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
                                  all_domains=all_domain_list, n=n*n, occupation=con_dict[variable])
                agents.append(agent)
                i += 1
                #agent.start()

        for agent in agents:
            agent.start()

        # for agent in agents:
        #     if occupation_dict[agent.name] is not None:
        #         agent.send_message(agent.task_queue, "startagent", {"identifier": [],
        #                                                         "sender": [], "occupation": occupation_dict})
        agents[7].send_message(agents[0].task_queue, "startagent", {"identifier": [],
                                                                    "sender": [], "occupation": occupation_dict})
        print(f"Start {time.time()}")
        #for agent in agents:
        #    agent.send_message(agent.task_queue, "kill", {"kill": ""})

        log_queue.close()
        for agent in agents:
            agent.join()

