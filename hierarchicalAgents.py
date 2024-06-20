import json
from multiprocessing import Process
import time
from UnitTest import read_sudoku


class HA_Coordinator(Process):
    def __init__(self, coordinator_queue, connections, domains, csp_numbers, con_dict, *args, **kwargs):
        super(HA_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.connections = connections
        self.domains = domains
        self.con_dict = con_dict
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = csp_numbers

        self.solving_time = 0

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "start": self.handle_start
        }

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = {"header": header, "message": message}
        recipient_queue.put((self.name, self.csp_number, message_data))

    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            print(f"{self.name} received unknown message type: {header} with message: {message}")

    def run(self):
        while self.running:
            if not self.coordinator_queue.empty():
                sender, csp_id, message_data = self.coordinator_queue.get()
                if csp_id == self.csp_number:
                    self.receive_message(message_data["header"], message_data["message"])

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.occupation = read_sudoku(self.csp_number + 1)
            self.solving_time = time.perf_counter() * 1000
            for connection in self.connections.keys():
                message = {"domains": self.domains, "occupation": self.occupation,
                            "csp_number": self.csp_number + 1}
                self.send_message(self.connections[connection], "startagent", message)
            print(f"Starting CSP {self.csp_number + 1}")
            self.csp_number += 1
        else:
            print("All CSPs solved.")
            for connection in self.connections.keys():
                if connection != "coordinator":
                    self.send_message(self.connections[connection], "kill", {"kill": ""})
            self.running = False


class HierarchicalAttributAgent(Process):
    def __init__(self, agent_id, log_queue, name, connections, constraints, all_domains,
                 occupation, n=4, *args, **kwargs):
        super(HierarchicalAttributAgent, self).__init__()
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
        self.start_time = None
        self.end_time = None
        self.csp_number = 0

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
            print("Error: last_sender")

    def kill_all(self):
        # Beendet alle Agenten
        for connection in self.connections:
            self.send_message(self.connections[connection], "kill", {"kill": ""})

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = {"header": header, "message": message}
        recipient_queue.put((self.name, self.csp_number, message_data))

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
            self.send_message(self.connections[self.last_sender(communicationDict["sender"])], "nogood",
                              communicationDict)
            return

        if i == 0:
            self.send_random(communicationDict)

    def send_random(self, communicationDict):
        # Sendet eine Nachricht an einen zufälligen nicht gesetzten Agenten
        for agent in communicationDict["occupation"]:
            if communicationDict["occupation"][agent] is None:
                self.send_message(self.connections[agent], "check", communicationDict)
                return
        print(communicationDict["occupation"])
        self.kill_all()

    def stop(self, message):
        # Beendet den Agenten
        #self.log("Received kill message.")
        #self.log("Stopping agent.")
        #self.join()
        self.end_time = time.perf_counter() * 1000
        self.running = False
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            print(f"Zeit für die Lösung: {duration} ms")
        # print(f"Agent {self.agent_id} ({self.name}) stopped.")

    def startagent(self, communicationDict):
        # Startet den Agenten
        #self.log("Received start message.")
        #self.log("Starting agent.")
        self.start_time = time.perf_counter() * 1000
        communicationDict["sender"].append("start")
        communicationDict["identifier"].append("start")
        self.check(communicationDict)

    # Löst alle Constraints mit den gegebenen Domains und findet valide Lösungsmenge
    def solve(self, constraintDict):
        list_domains = []
        for domain in self.all_domains:
            if self.is_valid(domain, self.name, constraintDict):
                list_domains.append(domain)
        return list_domains

    def is_valid(self, value, var, assigned_values):
        local_env = assigned_values.copy()
        local_env[var] = value
        for vari, func_constraint in self.constraints.items():
            modified_constraint = func_constraint
            for key in local_env:
                modified_constraint = modified_constraint.replace(key, str(local_env[key]))
            try:
                if not eval(modified_constraint):
                    return False
            except NameError:
                continue
        return True

    def run(self):
        while self.running:
            if not self.task_queue.empty():
                sender, csp_id, message_data = self.task_queue.get()
                if csp_id == self.csp_number:
                    self.receive_message(message_data["header"], message_data["message"])