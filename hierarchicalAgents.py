import json
from multiprocessing import Process
import time
from UnitTest import read_sudoku
import random


class HA_Coordinator(Process):
    def __init__(self, connections, domains, csp_numbers, con_dict, *args, **kwargs):
        super(HA_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = connections["coordinator"]
        self.connections = connections
        self.domains = domains
        self.con_dict = con_dict
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = csp_numbers

        self.data_collection = dict()
        self.collected_data = dict()

        self.solving_time = 0

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "unconfirm": self.handle_unconfirm,
            "start": self.handle_start,
            "ask_data": self.handle_data_collection
        }

    def prepare_dict(self):
        preparation_dict = dict()
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            preparation_dict[connection] = False
        # print(f"Preparation dict: {preparation_dict}")
        return preparation_dict

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
            self.collected_data = self.prepare_dict()
            occupation = read_sudoku(self.csp_number + 1)
            con_dict = self.fill_con_dict(occupation)
            self.occupation = occupation
            for connection in self.connections.keys():
                if connection == "coordinator":
                    continue
                if occupation[connection] is None:
                    message = {"domains": self.domains, "con_dict": con_dict[connection],
                               "csp_number": self.csp_number + 1, "active": True}
                    self.send_message(self.connections[connection], "new_start", message)
                else:
                    message = {"domains": self.domains, "con_dict": con_dict[connection],
                               "csp_number": self.csp_number + 1, "active": False}
                    self.send_message(self.connections[connection], "new_start", message)

            print(f"Starting CSP {self.csp_number + 1}")
            self.solving_time = time.perf_counter() * 1000
            self.csp_number += 1
            for key in self.occupation:
                if self.occupation[key] is None:
                    self.send_message(self.connections[key], "start_solving",
                                      {"occupation": self.occupation, "sender": [], "identifier": []})
                    return
        else:
            print("All CSPs solved.")
            for connection in self.connections.keys():
                if connection != "coordinator":
                    self.send_message(self.connections[connection], "kill", {"kill": ""})
            self.running = False

    def ask_data(self):
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            self.send_message(self.connections[connection], "ask_data", {"sender": self.name})

    def fill_con_dict(self, occupation):
        new_con_dict = self.con_dict.copy()
        for key in new_con_dict:
            for key2 in new_con_dict[key]:
                new_con_dict[key][key2] = occupation[key2]
        return new_con_dict

    def handle_unconfirm(self, message):
        return
        # print("No solution found.")
        # end_time = time.perf_counter() * 1000
        # duration = end_time - self.solving_time
        # print("Zeit für die Lösung:", duration, "ms")
        # self.ask_data()

    def handle_confirm(self, message):
        print(f"Solution found: {message['occupation']}")
        end_time = time.perf_counter() * 1000
        duration = end_time - self.solving_time
        print("Zeit für die Lösung:", duration, "ms")
        self.ask_data()

    def handle_data_collection(self, message):
        for key in message.keys():
            if key == "sender":
                continue
            self.data_collection[key] = self.data_collection.get(key, 0) + message[key]
        self.collected_data[message["sender"]] = True
        if all(self.collected_data.values()):
            print(f"Die Daten des CSP: {self.data_collection}")
            self.next_csp()

    def handle_start(self, message):
        print("Starting coordinator")
        self.number_of_csp = int(message["number_of_csp"])
        self.next_csp()


class HierarchicalAttributAgent(Process):
    def __init__(self, agent_id, name, connections, constraints, *args, **kwargs):
        super(HierarchicalAttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten
        self.name = name  # Name des Agenten
        self.task_queue = connections[self.name]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = None  # Liste aller möglicher eigener Domains
        self.nogood_dict = None  # Dictionary mit No-goods Key: Constraint-String Value: Liste von no-good Domains
        self.agent_view = None  # Dictionary mit den Domains, die der Agent betrachtet
        self.occupation = None  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen

        self.csp_number = 0
        self.data_collection_dict = dict()

        self.message_handlers = {
            "check": self.handle_check,
            "nogood": self.handle_nogood,
            "kill": self.handle_stop,
            "start_solving": self.handle_start_solving,
            "ask_data": self.handle_data_collection,
            "new_start": self.handle_new_start
        }

    def unit_testing(self, occupation, domains):
        # Testet die Constraints mit den gegebenen Domains und eliminiert invalide Domains
        set_domain = set()
        for key in occupation:
            if occupation[key] is not None:
                set_domain.add(occupation[key])

        list_domain = []
        for domain in domains:
            if domain not in set_domain:
                list_domain.append(domain)
        if len(list_domain) == 0:
            print(f"{self.name} No solution found.")
            print(f"{self.name} occupation: {occupation} and domains: {domains}")
            # self.kill_all()
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
        # Beendet Solving, da keine Lösung gefunden wurde
        self.send_message(self.connections["coordinator"], "unconfirm", {"kill": ""})

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        self.data_collection_dict[header] = self.data_collection_dict.get(header, 0) + 1
        message_data = {"header": header, "message": message}
        recipient_queue.put((self.name, self.csp_number, message_data))

    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            print(f"Received unknown message type: {header} with message: {message}")
            # self.log(f"Received unknown message type: {header} with message: {message}")

    def handle_nogood(self, communicationDict):
        # Aktualisiert das Dictionary der No-goods und probiert die Constraints mit einer neuen Domain
        # zu erfüllen ansonsten wird eine "nogood"-Nachricht an den vorherigen Agenten gesendet
        # self.log(f"Received nogood from {constraintDict['identifier']}")
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
            self.data_collection_dict["solution_changed"] = self.data_collection_dict.get("solution_changed", 0) + 1
            for key in self.occupation:
                if communicationDict["occupation"][key] is None:
                    self.send_message(self.connections[key], "check", communicationDict)
                    a += 1
                    # print(f"{self.name} is sending other check to {key} and"
                    #       f" Domain: {communicationDict['occupation'][self.name]}")
                    return

    def handle_check(self, communicationDict):
        # Überprüft, ob es eine Möglichkeit gibt die Constraints zu erfüllen mit
        # den aktuellen Domains-String und fragt die anderen nicht im Domain-String
        # enthaltenen Agenten, ob die Auswahl gültig ist
        if communicationDict["identifier"][-1] == "start":
            hash_identifier = hash("start")
            occ_dict = self.occupation
        else:
            occ_dict, hash_identifier = self.occupation_hash(communicationDict["occupation"])

        if hash_identifier not in self.agent_view and hash_identifier not in self.nogood_dict:
            solve_list = self.solve(communicationDict["occupation"])
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
            self.agent_view[hash_identifier].update(self.nogood_dict[hash_identifier])
            self.nogood_dict[hash_identifier] = set()

        i = True
        if len(self.agent_view[hash_identifier]) != 0:
            communicationDict["identifier"].append(hash_identifier)
            communicationDict["occupation"][self.name] = self.agent_view[hash_identifier].pop()
            self.data_collection_dict["solution_changed"] = self.data_collection_dict.get("solution_changed", 0) + 1
            communicationDict["sender"].append(self.name)
            none_keys = [key for key in occ_dict if communicationDict["occupation"][key] is None]
            if none_keys:
                random_key = random.choice(none_keys)
                self.send_message(self.connections[random_key], "check", communicationDict)
                i = False
        else:
            communicationDict["identifier"].pop()
            communicationDict["sender"].pop()
            communicationDict["occupation"][self.name] = None
            self.send_message(self.connections[self.last_sender(communicationDict["sender"])], "nogood",
                              communicationDict)
            i = False

        if i:
            self.send_random(communicationDict)

    def handle_data_collection(self, message):
        new_message = self.data_collection_dict.copy()
        new_message["sender"] = self.name
        self.send_message(self.connections["coordinator"], "ask_data", new_message)

    def send_random(self, communicationDict):
        # Sendet eine Nachricht an einen zufälligen nicht gesetzten Agenten
        for agent in communicationDict["occupation"]:
            if communicationDict["occupation"][agent] is None:
                self.send_message(self.connections[agent], "check", communicationDict)
                return
        self.send_message(self.connections["coordinator"], "confirm", communicationDict)

    def handle_stop(self, message):
        # Beendet den Agenten
        self.running = False

    def handle_new_start(self, message):
        self.data_collection_dict = dict()
        self.csp_number = message["csp_number"]
        if message["active"]:
            self.nogood_dict = dict()
            self.agent_view = dict()
            self.occupation = message["con_dict"]
            self.all_domains = self.unit_testing(message["con_dict"], message["domains"])
            random.shuffle(self.all_domains)

    def handle_start_solving(self, communicationDict):
        # Startet den Agenten
        communicationDict["sender"].append("start")
        communicationDict["identifier"].append("start")
        self.handle_check(communicationDict)

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
