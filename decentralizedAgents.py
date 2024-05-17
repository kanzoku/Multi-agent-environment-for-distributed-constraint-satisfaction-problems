import json
from multiprocessing import Process
import random

class DecentralizedAttributAgent(Process):
    def __init__(self, agent_id, coordinator_queue, name, connections, constraints, *args, **kwargs):
        super(DecentralizedAttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten zur Prioritätsermittlung
        self.name = name  # Name des Agenten
        self.coordinator_queue = coordinator_queue  # Queue für Log-Nachrichten
        self.task_queue = connections[self.name]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = None  # Liste aller möglicher eigener Domains
        self.nogood_set = set()  # Set mit No-goods des Agenten
        self.agent_view_dict = dict()  # Dictionary mit den Domains, die der Agent betrachtet
        self.agent_view_preparation_dict = self.prepare_agent_view()  # vorgefertigtes Dictionary für
        # Antworten auf die betrachteten Domains
        self.occupation = None  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen
        self.selected_value = None  # Ausgewählter Wert des Agenten
        self.list_run = 0  # Anzahl der Durchläufe
        self.csp_number = 0  # Kennung des gerade bearbeitenden CSP
        self.confirmed = False  # Flag, ob der Agent bestätigt hat

        self.message_handlers = {
            "must_be": self.handle_must_be,
            "check": self.handle_check,
            "good": self.handle_good,
            "backtrack": self.handle_backtrack,
            "nogood": self.handle_nogood,
            "kill": self.handle_stop,
            "startagent": self.handle_startagent
        }

    def prepare_agent_view(self):
        prepared_dict = dict()
        for connection in self.constraints.keys():
            prepared_dict[connection] = None
        return prepared_dict

    def domain_propagation(self):
        self.all_domains = [
            domain for domain in self.all_domains
            if all(
                self.occupation[connection] is None or self.is_valid(domain, connection, self.occupation[connection])
                for connection in self.constraints.keys()
            )
        ]

    def must_be_check(self):
        if len(self.all_domains) != 1:
            return False

        self.selected_value = self.all_domains[0]
        message = {"sender": self.name, "value": self.selected_value}
        self.send_message(self.coordinator_queue, "must_be", message)

        for connection in self.constraints.keys():
            self.send_message(self.connections[connection], "must_be", message)

        return True


    def is_valid(self, value, var, assigned_value):
        local_env = {var: assigned_value, self.name: value}
        modified_constraint = self.constraints[var]
        for key, val in local_env:
            modified_constraint = modified_constraint.replace(key, str(val))
        try:
            return eval(modified_constraint)
        except (SyntaxError, NameError, TypeError):
            return False

    def select_value(self):
        nogood_set = self.nogood_set
        agent_view_keys = self.agent_view_dict.keys()

        for value in self.all_domains:
            if value not in nogood_set and value not in agent_view_keys:
                self.agent_view_dict[value] = self.agent_view_preparation_dict
                self.selected_value = value
                return value

        self.nogood_set.clear()
        self.agent_view_dict.clear()
        self.list_run += 1

        self.backtrack()

        first_value = self.all_domains[0]
        self.agent_view_dict[first_value] = self.agent_view_preparation_dict
        self.selected_value = first_value
        return self.selected_value

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = json.dumps({"header": header, "message": message})
        recipient_queue.put((self.name, self.csp_number, message_data))

    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            print(f"Received unknown message type: {header} with message: {message}")

    def handle_must_be(self, message):
        # Füge die empfangene Domain zur Liste der belegten Domains hinzu
        self.occupation[message["sender"]] = message["value"]
        self.domain_propagation()
        if not self.must_be_check():
            self.check()

    def handle_stop(self, message):
        self.running = False

    def handle_startagent(self, message):
        shuffled_domains = message["domains"]
        random.shuffle(shuffled_domains)
        self.all_domains = shuffled_domains
        self.occupation = message["occupation"]
        self.csp_number = message["csp_number"]
        self.list_run = 0
        self.domain_propagation()
        if not self.must_be_check():
            self.check()

    def handle_check(self, message):
        if self.is_valid(self.selected_value, message["sender"], message["value"]):
            self.send_message(self.connections[message["sender"]], "good",
                              {"sender": self.name, "id": self.agent_id, "value": message["value"]})
        else:
            if self.agent_id > message["id"]:
                self.send_message(self.connections[message["sender"]], "nogood",
                                  {"sender": self.name, "id": self.agent_id, "value": message["value"]})
            else:
                self.agent_view_dict.pop(self.selected_value, None)
                self.nogood_set.add(self.selected_value)
                self.check()

    def handle_good(self, message):
        if self.agent_view_dict.__contains__(message["value"]):
            self.agent_view_dict[message["value"]][message["sender"]] = True
            if all(self.agent_view_dict[message["value"]].values()):
                self.send_message(self.coordinator_queue, "confirm",
                                  {"sender": self.name, "value": message["value"]})
                self.confirmed = True

    def handle_nogood(self, message):
        self.agent_view_dict.pop(message["value"], None)
        self.nogood_set.add(message["value"])
        self.check()

    def handle_backtrack(self, message):
        if self.agent_id < message["id"]:
        return

    def backtrack(self):
        for connection in self.constraints.keys():
            self.send_message(self.connections[connection], "backtrack",
                              {"sender": self.name, "id": self.agent_id, "value_list": self.all_domains})

    def check(self):
        self.select_value()
        for connection in self.constraints.keys():
            self.send_message(self.connections[connection], "check",
                              {"sender": self.name, "id": self.agent_id, "value": self.selected_value})

    def run(self):
        while self.running:
            if not self.task_queue.empty():
                sender, csp_id, message = self.task_queue.get()
                if csp_id == self.csp_number:
                    message = json.loads(message)
                    self.receive_message(message["header"], message["message"])
