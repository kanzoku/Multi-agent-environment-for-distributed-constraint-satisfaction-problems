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
        self.nogood_list = list()  # Liste mit No-goods des Agenten
        self.agent_view = list()  # Liste mit den Domains, die der Agent betrachtet
        self.occupation = None  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen
        self.selected_value = None  # Ausgewählter Wert des Agenten
        self.list_run = 0  # Anzahl der Durchläufe
        self.csp_number = 0  # Kennung des gerade bearbeitenden CSP

        self.message_handlers = {
            "must_be": self.handle_must_be,
            "check": self.handle_check,
            "good": self.handle_good,
            "nogood": self.handle_nogood,
            "kill": self.handle_stop,
            "startagent": self.handle_startagent
        }

    def domain_propagation(self):
        list_domains = []
        for domain in self.all_domains:
            if self.is_valid(domain, self.name, self.occupation):
                list_domains.append(domain)
        self.all_domains = list_domains



    def must_be_check(self):
        if len(self.all_domains) == 1:
            self.selected_value = self.all_domains[0]
            self.send_message(self.coordinator_queue, "must_be",
                              {"sender": self.name, "value": self.selected_value})
            for connection in self.constraints.keys():
                self.send_message(self.connections[connection], "must_be",
                                  {"sender": self.name, "value": self.selected_value})
            return True
        return False

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
        nogood_set = set(self.nogood_list)
        agent_view_set = set(self.agent_view)

        for value in self.all_domains:
            if value not in nogood_set and value not in agent_view_set:
                self.agent_view.append(value)
                self.selected_value = value
                return value

        self.nogood_list.clear()
        self.agent_view.clear()
        self.list_run += 1

        first_value = self.all_domains[0]
        self.agent_view.append(first_value)
        self.selected_value = first_value
        return self.selected_value

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
            self.send_message(self.coordinator_queue, "good",
                              {"sender": self.name, "id": self.agent_id, "value": self.selected_value})


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
