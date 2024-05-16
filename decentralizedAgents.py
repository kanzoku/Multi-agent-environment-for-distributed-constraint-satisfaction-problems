import json
from multiprocessing import Process

class DecentralizedAttributAgent(Process):
    def __init__(self, agent_id, coordinator_queue, name, connections, constraints, all_domains,
                 occupation, n=4, *args, **kwargs):
        super(DecentralizedAttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten zur Prioritätsermittlung
        self.name = name  # Name des Agenten
        self.coordinator_queue = coordinator_queue  # Queue für Log-Nachrichten
        self.task_queue = connections[self.name]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = all_domains  # Liste aller möglicher eigener Domains
        self.nogood_list = list()  # Liste mit No-goods des Agenten
        self.agent_view = list()  # Liste mit den Domains, die der Agent betrachtet
        self.occupation = occupation  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen

        self.message_handlers = {
            "must_be": self.must_be,
            "check": self.check,
            "nogood": self.nogood,
            "kill": self.stop,
            "startagent": self.startagent
        }

    def domain_propagation(self):
        list_domains = []
        for domain in self.all_domains:
            if self.is_valid(domain, self.name, self.occupation):
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

    def select_value(self):
        for value in self.all_domains:
            if value not in self.nogood_list:
                self.agent_view.append(value)
                return value
        self.nogood_list.clear()
        self.agent_view.append(self.all_domains[0])
        return self.all_domains[0]

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

    def must_be(self, message):
        # Füge die empfangene Domain zur Liste der belegten Domains hinzu
        self.occupation[message["sender"]] = message["value"]
        self.domain_propagation()
