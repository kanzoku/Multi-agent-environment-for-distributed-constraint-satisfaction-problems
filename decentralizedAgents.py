from multiprocessing import Process
import random
from UnitTest import read_sudoku
import time


class DA_Coordinator(Process):
    def __init__(self, coordinator_queue, connections, domains, csp_numbers, con_dict, *args, **kwargs):
        super(DA_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.connections = connections
        self.domains = domains
        self.con_dict = con_dict
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = csp_numbers
        self.data_collection = dict()
        self.collected_data = dict()
        self.filter = True

        self.solving_time = 0

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "unconfirm": self.handle_unconfirm,
            "start": self.handle_start,
            "ask_data": self.handle_data_collection
        }

    def prepare_collected_data(self):
        i = 1
        for connection in self.connections.keys():
            if connection != "coordinator":
                self.collected_data[i] = False
                i += 1
        print(f"Prepared collected data: {self.collected_data}")

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

    def handle_confirm(self, message):
        if not self.filter:
            return
        self.occupation[message["sender"]] = message["value"]
        # print(f"Confirmed: {message['sender']} with value {message['value']}")
        if all([value is not None for value in self.occupation.values()]):
            end_time = time.perf_counter() * 1000
            duration = end_time - self.solving_time
            self.filter = False
            print(f"Solution found: {self.occupation}")
            print("Zeit für die Lösung:", duration, "ms")
            self.ask_data()

    def handle_data_collection(self, message):
        for key in message.keys():
            if key == "sender":
                continue
            self.data_collection[key] = self.data_collection.get(key, 0) + message[key]
        # print(f"Data collected from {message['sender']}")
        self.collected_data[message["sender"]] = True
        if all(self.collected_data.values()):
            print(f"Die Daten des CSP: {self.data_collection}")
            self.next_csp()

    def handle_unconfirm(self, message):
        # print(f"Unconfirmed: {message['sender']} with value {self.occupation[message['sender']]}")
        if self.filter:
            self.occupation[message["sender"]] = None

    def handle_start(self, message):
        print("Starting coordinator")
        self.next_csp()

    def ask_data(self):
        print("Asking for data")
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            self.send_message(self.connections[connection], "ask_data", {"sender": self.name})

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.prepare_collected_data()
            self.filter = True
            self.data_collection.clear()
            self.occupation = read_sudoku(self.csp_number+1)
            self.solving_time = time.perf_counter() * 1000
            for connection in self.connections.keys():
                message = {"domains": self.domains, "occupation": self.occupation,
                           "csp_number": self.csp_number + 1}
                self.send_message(self.connections[connection], "startagent", message)
            print(f"Starting CSP {self.csp_number + 1}")
            self.csp_number += 1
        else:
            self.running = False

    def run(self):
        while self.running:
            if not self.coordinator_queue.empty():
                sender, csp_id, message_data = self.coordinator_queue.get()
                if csp_id == self.csp_number:
                    # message = json.loads(message)
                    self.receive_message(message_data["header"], message_data["message"])


class DecentralizedAttributAgent(Process):
    def __init__(self, agent_id, name, coordinator_queue, connections, constraints, *args, **kwargs):
        super(DecentralizedAttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten zur Prioritätsermittlung
        self.name = name  # Name des Agenten
        self.coordinator_queue = coordinator_queue  # Queue für Coordinator-Nachrichten
        self.task_queue = connections[self.name]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = None  # Liste aller möglicher eigener Domains
        self.nogood_set = set()  # Set mit No-goods des Agenten
        self.backtrack_set = set()  # Set mit Backtrack-Values des Agenten
        self.agent_view_dict = dict()  # Dictionary mit den Domains, die der Agent betrachtet
        self.agent_view_preparation_dict = self.prepare_agent_view()  # vorgefertigtes Dictionary für
        # Antworten auf die betrachteten Domains
        self.occupation = None  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen
        self.selected_value = None  # Ausgewählter Wert des Agenten
        self.list_run = 0  # Anzahl der Durchläufe
        self.csp_number = 0  # Kennung des gerade bearbeitenden CSP
        self.confirmed = False  # Flag, ob der Agent bestätigt hat
        self.data_collection_dict = dict()  # Dictionary für die Datensammlung

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "must_be": self.handle_must_be,
            "check": self.handle_check,
            "good": self.handle_good,
            "backtrack": self.handle_backtrack,
            "nogood": self.handle_nogood,
            "kill": self.handle_stop,
            "startagent": self.handle_startagent,
            "ask_data": self.handle_data_collection
        }

    # Erstellt ein Dictionary für die Vorbereitung des Agenten-Views
    def prepare_agent_view(self):
        prepared_dict = dict()
        for connection in self.constraints.keys():
            prepared_dict[connection] = False
        return prepared_dict

    def get_nogood_value_for_backtrack(self):
        if len(self.nogood_set - self.backtrack_set) == 0:
            self.backtrack_set.clear()
        while True:
            if len(self.nogood_set) == 0:
                chosen_value = random.choice(list(self.all_domains))
                break
            else:
                chosen_value = random.choice(list(self.nogood_set))
                if chosen_value not in self.backtrack_set:
                    break
        self.backtrack_set.add(chosen_value)
        self.nogood_set.remove(chosen_value)
        return chosen_value

    # Schließt die Domänen aus, die nicht mehr infrage kommen
    def domain_propagation(self, agent_name=None):
        if agent_name is not None:
            self.all_domains = [
                domain for domain in self.all_domains
                if self.is_valid(domain, agent_name, self.occupation[agent_name])
            ]
        else:
            self.all_domains = [
                domain for domain in self.all_domains
                if all(
                    self.occupation[connection] is None or self.is_valid(domain, connection,
                                                                         self.occupation[connection])
                    for connection in self.constraints.keys()
                )
            ]

    # Überprüft, ob der Agent einen eindeutigen Wert in der Domäne hat
    def must_be_check(self):
        if len(self.all_domains) != 1:
            return False

        self.selected_value = self.all_domains[0]
        self.confirmed = True
        message = {"sender": self.name, "value": self.selected_value}
        self.send_message(self.coordinator_queue, "confirm", message)

        for connection in self.constraints.keys():
            self.send_message(self.connections[connection], "must_be", message)
        # print(f"Must be: {self.name} with value {self.selected_value}")
        return True

    # Solver zur Überprüfung der Constraints
    def is_valid(self, value, var, assigned_value):
        local_env = {var: assigned_value, self.name: value}
        modified_constraint = self.constraints[var]
        for key, val in local_env.items():
            modified_constraint = modified_constraint.replace(key, str(val))
        try:
            return eval(modified_constraint)
        except (SyntaxError, NameError, TypeError):
            return False

    # Wählt einen Wert aus der Domäne aus, der noch nicht in der No-good-Liste oder im Agenten-View ist
    def select_value(self):
        nogood_set = self.nogood_set
        agent_view_keys = self.agent_view_dict.keys()
        for value in self.all_domains:
            if value not in nogood_set and value not in agent_view_keys:
                self.agent_view_dict[value] = self.agent_view_preparation_dict
                self.selected_value = value
                self.data_collection_dict["solution_changed"] = self.data_collection_dict.get("solution_changed", 0) + 1
                return True
        return False

    # Sendet Nachrichten an andere Agenten
    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        self.data_collection_dict[header] = self.data_collection_dict.get(header, 0) + 1
        message_data = {"header": header, "message": message}
        recipient_queue.put((self.name, self.csp_number, message_data))

    # Empfängt Nachrichten von anderen Agenten und bearbeitet sie weiter
    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            try:
                handler(message)  # Rufe die zugehörige Funktion auf
            except Exception as e:
                print(f"Error in {self.name} with message {message}")
                print(e)
        else:
            print(f"Received unknown message type: {header} with message: {message}")

    def handle_data_collection(self, message):
        new_message = self.data_collection_dict.copy()
        new_message["sender"] = self.agent_id
        self.send_message(self.connections["coordinator"], "ask_data", new_message)

    # Behandelt Must-be-Nachrichten, um eindeutige Werte zu confirmen und die Domäne-Menge zu aktualisieren
    def handle_must_be(self, message):
        # Füge die empfangene Domain zur Liste der belegten Domains hinzu
        self.occupation[message["sender"]] = message["value"]
        if len(self.all_domains) > 1:
            self.domain_propagation(agent_name=message["sender"])
            if not self.must_be_check():
                self.agent_view_dict.clear()
                self.nogood_set.clear()
                self.list_run += 1
                self.check()

    # Behandelt Stop-Nachrichten, um den Agenten zu stoppen
    def handle_stop(self, message):
        self.running = False

    # Behandelt Startagent-Nachrichten, um mehrere Durchläufe zu ermöglichen, ohne die Agenten neu zu starten
    def handle_startagent(self, message):
        self.data_collection_dict.clear()
        if message["occupation"][self.name] is None:
            shuffled_domains = message["domains"]
            random.shuffle(shuffled_domains)
            self.all_domains = shuffled_domains
            self.occupation = message["occupation"]
            self.csp_number = message["csp_number"]
            self.list_run = 0
            self.domain_propagation()
            # print(f"Starting agent {self.name} with domains {self.all_domains}")
        else:
            self.csp_number = message["csp_number"]
            self.all_domains = [message["occupation"][self.name]]
            self.occupation = message["occupation"]

        self.must_be_check()
        if self.agent_id == 1:
            self.check()
        else:
            self.select_value()

    # Behandelt Check-Nachrichten, dabei wird überprüft, ob der Wert des sendenden Agenten gültig ist,
    # ansonsten werden Maßnahmen ergriffen, um einen gültigen Wert zu finden
    def handle_check(self, message):
        if self.is_valid(self.selected_value, message["sender"], message["value"]):
            self.send_message(self.connections[message["sender"]], "good",
                              {"sender": self.name, "id": self.agent_id, "value": message["value"],
                               "list_run": message["list_run"]})
        else:
            if message["id"] < self.agent_id and len(self.all_domains) > 1:
                self.send_message(self.connections[message["sender"]], "good",
                                  {"sender": self.name, "id": self.agent_id, "value": message["value"],
                                   "list_run": message["list_run"]})
                self.agent_view_dict.clear()
                self.nogood_set.clear()
                self.nogood_set.add(message["value"])
                self.list_run += 1
                if self.confirmed:
                    self.confirmed = False
                    self.send_message(self.coordinator_queue, "unconfirm",
                                      {"sender": self.name, "value": self.selected_value})
                self.check()
            else:
                self.send_message(self.connections[message["sender"]], "nogood",
                                  {"sender": self.name, "id": self.agent_id, "value": message["value"],
                                   "list_run": message["list_run"]})

    # Behandelt Good-Nachrichten, dabei wird der boolean Wert für den Agenten in der Domäne auf True gesetzt und
    # sollten alle True sein wird die Domäne confirmed
    def handle_good(self, message):
        if message["list_run"] == self.list_run and self.agent_view_dict.__contains__(message["value"]):
            self.agent_view_dict[message["value"]][message["sender"]] = True
            if all(self.agent_view_dict[message["value"]].values()):
                # print(f"Good: {self.name} with value {message['value']}")
                self.send_message(self.coordinator_queue, "confirm",
                                  {"sender": self.name, "value": message["value"]})
                self.confirmed = True

    # Behandelt No-good-Nachrichten, dabei wird der Wert aus der betrachteten Domains entfernt
    # und in die No-good-Liste eingefügt
    def handle_nogood(self, message):
        if message["list_run"] == self.list_run:
            if self.agent_view_dict.__contains__(message["value"]):
                # print(f"No good: {self.name} with value {message['value']} from {message['sender']}")
                self.agent_view_dict.pop(message["value"], None)
                # print(f"No good: {self.name} with value {message['value']}")
                self.nogood_set.add(message["value"])
                self.check()

    # Behandelt Backtrack-Nachrichten, dabei werden die Domains des Agenten mit den Domains des sendenden Agenten
    # verglichen und sollte der selektierte Wert in der Schnittmenge liegen, wird der Agent zurückgesetzt und ein
    # neuer Check wird durchgeführt
    def handle_backtrack(self, message):
        if len(self.all_domains) > 1:
            if self.selected_value is message["value"]:
                # print(f"Had to Backtrack: {self.name} with value {self.selected_value}")
                if self.confirmed:
                    self.confirmed = False
                    self.send_message(self.coordinator_queue, "unconfirm",
                                      {"sender": self.name, "value": self.selected_value})
                self.agent_view_dict.clear()
                self.nogood_set.clear()
                self.nogood_set.add(self.selected_value)
                self.check()

    # Sendet Nachrichten an andere Agenten, um einen Backtrack zu starten
    def backtrack(self):
        backtrack_value = self.get_nogood_value_for_backtrack()
        # print(f"Backtrack: {self.name} to value {backtrack_value}")
        for connection in self.constraints.keys():
            self.send_message(self.connections[connection], "backtrack",
                              {"sender": self.name, "id": self.agent_id, "value": backtrack_value})
        self.agent_view_dict.clear()
        self.list_run += 1
        self.check()

    # Überprüft, ob der Agent einen Wert auswählen kann
    def check(self):
        if self.select_value():
            # print(f"Check: {self.name} with value {self.selected_value}")
            for connection in self.constraints.keys():
                self.send_message(self.connections[connection], "check",
                                  {"sender": self.name, "id": self.agent_id, "value": self.selected_value,
                                   "list_run": self.list_run})
        else:
            self.backtrack()

    # Hauptloop des Agenten
    def run(self):
        while self.running:
            if not self.task_queue.empty():
                sender, csp_id, message_data = self.task_queue.get()
                if csp_id == self.csp_number:
                    self.receive_message(message_data["header"], message_data["message"])
