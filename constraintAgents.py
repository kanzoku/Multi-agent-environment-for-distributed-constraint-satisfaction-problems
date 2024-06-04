import json
from multiprocessing import Process
import random
import itertools
from UnitTest import read_sudoku


class CA_Coordinator(Process):
    def __init__(self, coordinator_queue, connections, domains, csp_numbers, con_dict, *args, **kwargs):
        super(CA_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.connections = connections
        self.domains = domains
        self.con_dict = con_dict
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = csp_numbers

        self.prepared_dict = self.prepare_dict()
        self.status_dict = dict()
        self.possibilities = dict()

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "start": self.handle_start
        }

    def prepare_dict(self):
        preparation_dict = dict()
        for connection in self.connections.keys():
            preparation_dict[connection] = None
        return preparation_dict

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
            print(f"{self.name} received unknown message type: {header} with message: {message}")

    def handle_confirm(self, message):
        if all([value is not None for value in self.occupation.values()]):
            print(f"Solution found: {self.occupation}")
            self.next_csp()

    def handle_start(self, message):
        print("Starting coordinator")
        self.next_csp()

    def handle_propagation(self, message):
        if message["sender"] in self.status_dict:
            self.status_dict[message["sender"]] = True
            if all(self.status_dict.values()):
                self.all_propagations_true()

    def handle_ask_possibilities(self, message):
        if message["sender"] in self.status_dict:
            self.possibilities[message["sender"]] = message["possibilities"]
            if all(isinstance(value, int) for value in self.status_dict.values()):
                self.solve()

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.occupation = read_sudoku(self.csp_number)
            self.status_dict = self.prepared_dict
            self.possibilities = self.prepared_dict
            # self.occupation = {'a1': 2, 'a2': None, 'a3': None, 'a4': 1, 'b1': None, 'b2': 3, 'b3': None, 'b4': None,
            #                    'c1': None, 'c2': None, 'c3': 4, 'c4': None, 'd1': None, 'd2': None, 'd3': None, 'd4': None}
            for connection in self.connections.keys():
                message = {"domains": self.domains, "occupation": self.occupation,
                           "csp_number": self.csp_number + 1}
                self.send_message(self.connections[connection], "startagent", message)
            self.csp_number += 1
        else:
            self.running = False

    def all_propagations_true(self):
        for connection in self.connections.keys():
            self.send_message(self.connections[connection], "ask_possibilities", {"sender": self.name})
        pass

    def solve(self):
        ranking, start = self.sort_and_create_sender_dict(self.possibilities)
        if start is not None:
            self.send_message(self.connections[start], "start_solve", {"sender": self.name,
                                                                 "ranking": ranking, "occupation": self.occupation})
        else:
            print("No start found")

    def sort_and_create_sender_dict(self, data, order='asc'):
        if order == 'asc':
            sorted_data = dict(sorted(data.items(), key=lambda item: item[1]))
        elif order == 'desc':
            sorted_data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        elif order == 'random':
            sorted_data = dict(data)
            items = list(sorted_data.items())
            random.shuffle(items)
            sorted_data = dict(items)
        else:
            raise ValueError("Keine gültige Sortierreihenfolge angegeben")

        # Abarbeitungsliste erstellen
        result = {}
        start = None
        keys = list(sorted_data.keys())

        for i, key in enumerate(keys):
            if i == 0:
                last_sender = 'start'
                start = key
            else:
                last_sender = keys[i - 1]

            if i == len(keys) - 1:
                next_sender = 'end'
            else:
                next_sender = keys[i + 1]

            result[key] = {
                'lastSender': last_sender,
                'nextSender': next_sender
            }

        return result, start

    def run(self):
        while self.running:
            if not self.coordinator_queue.empty():
                sender, csp_id, message = self.coordinator_queue.get()
                if csp_id == self.csp_number:
                    message = json.loads(message)
                    self.receive_message(message["header"], message["message"])

class ConstraintAgent(Process):
    def __init__(self, agent_id, coordinator_queue, name, connections, constraint, *args, **kwargs):
        super(ConstraintAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten zur Prioritätsermittlung
        self.coordinator_queue = coordinator_queue  # Queue für Coordinator-Nachrichten
        self.task_queue = connections[self.agent_id]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraint = constraint  # String mit den Constraint des Agenten
        self.all_domains = None  # Dictionary
        self.all_domain_list = None
        self.possibilities = 0
        self.nogood_list = list()  # Liste mit No-goods des Agenten die eine Kombination blockieren
        self.agent_view_dict = dict()  # Dictionary mit den Domains, die der Agent betrachtet
        # self.agent_view_preparation_dict = self.prepare_agent_view()  # vorgefertigtes Dictionary für
        # Antworten auf die betrachteten Domains
        self.occupation = None  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen
        self.selected_values = None  # Ausgewählter Wert des Agenten
        self.list_run = 0  # Anzahl der Durchläufe
        self.csp_number = 0  # Kennung des gerade bearbeitenden CSP
        self.confirmed = False  # Flag, ob der Agent bestätigt hat

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "check": self.handle_check,
            "domain_propagation": self.handle_domain_propagation,
            "nogood": self.handle_nogood,
            "kill": self.handle_stop,
            "startagent": self.handle_startagent,
            "ask_possibilities": self.handle_ask_possibilities,
        }

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = json.dumps({"header": header, "message": message})
        recipient_queue.put((self.agent_id, self.csp_number, message_data))

    # Empfängt Nachrichten von anderen Agenten und bearbeitet sie weiter
    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            print(f"Received unknown message type: {header} with message: {message}")

    # Hauptloop des Agenten
    def run(self):
        while self.running:
            if not self.task_queue.empty():
                sender, csp_id, message = self.task_queue.get()
                if csp_id == self.csp_number:
                    self.receive_message(message["header"], message["message"])

    def domain_propagation(self):
        domain_set = set(self.all_domain_list)
        for key in self.all_domains.keys():
            if self.occupation[key] is not None:
                self.all_domains[key] = [self.occupation[key]]
                domain_set.remove(self.occupation[key])

        domain_list = list(domain_set)

        for key in self.all_domains.keys():
            if self.all_domains[key] is None:
                self.all_domains[key] = domain_list

        for connection in self.connections.keys():
            if connection != self.agent_id and connection != "coordinator":
                message = {"domains": self.all_domains}
                self.send_message(self.connections[connection], "domain_propagation", message)

        self.send_message(self.coordinator_queue, "domain_propagation", {"sender": self.name})

    def find_valid_solution(self, occupation):
        copy_all_domains = self.all_domains.copy()
        for key in copy_all_domains.keys():
            if occupation[key] is not None and occupation[key] in copy_all_domains[key]:
                copy_all_domains[key] = [occupation[key]]

            if len(copy_all_domains[key]) == 0:
                return False

        solution = self.solver(copy_all_domains)
        if solution:
            self.selected_values = solution
            return True
        else:
            return False

    def solver(self, domain_dict):
        keys = domain_dict.keys()
        values = itertools.product(*domain_dict.values())
        for combination in values:
            if self.is_blocked_combination(combination, keys):
                continue

            if len(set(combination)) != len(combination):
                continue

            expr_copy = self.constraint
            for key, value in zip(keys, combination):
                expr_copy = expr_copy.replace(key, str(value))
            try:
                result = eval(expr_copy)
                if result:
                    return {key: value for key, value in zip(keys, combination)}
            except Exception as e:
                continue
        return {}

    def is_blocked_combination(self, combination, keys):
        for blocked_condition in self.nogood_list:
            if all(combination[keys.index(k)] == v for k, v in blocked_condition.items()):
                return True
        return False

    def handle_domain_propagation(self, message):
        possibilities = 1
        for key in message["domains"].keys():
            if key in self.all_domains.keys():
                self.all_domains[key] = list(set(self.all_domains[key]) & set(message["domains"][key]))
                possibilities *= len(self.all_domains[key])
        self.possibilities = possibilities

    def handle_ask_possibilities(self, message):
        self.send_message(self.coordinator_queue, "possible", {"sender": self.agent_id,
                                                              "possibilities": self.possibilities})

    def handle_check(self, message):
        if self.find_valid_solution(message["occupation"]):
            message["occupation"] = self.add_solution(message["occupation"])
            nextReceiver = message["ranking"][self.agent_id]["nextSender"]
            if nextReceiver == "end":
                self.send_message(self.coordinator_queue, "confirm", {"sender": self.agent_id,
                                                                      "occupation": message["occupation"]})
            else:
                message["sender"] = self.agent_id

                self.send_message(self.connections[nextReceiver], "check", message)
        else:
            lastSender = message["ranking"][self.agent_id]["lastSender"]
            message["sender"] = self.agent_id
            message["domains"] = self.all_domains
            self.send_message(lastSender, "nogood", message)

    def handle_nogood(self, message):
        occ_dict = message["occupation"]
        nogood_combination = dict()
        for key in self.all_domains.keys():
            if key in message["domains"]:
                nogood_combination[key] = occ_dict[key]
                occ_dict[key] = None
        self.nogood_list.append(nogood_combination)
        self.check(occ_dict, message)


    def handle_stop(self, message):
        self.running = False

    def handle_startagent(self, message):
        pass

    def add_solution(self, occupation):
        for key in self.selected_values.keys():
            if occupation[key] is None:
                occupation[key] = self.selected_values[key]
        return occupation

    def remove_last_solution(self, occupation):
        for key in self.all_domains.keys():
            if key not in occupation:
                continue
            if len(self.all_domains[key]) > 1:
                occupation[key] = None
            elif len(self.all_domains[key]) == 1:
                occupation[key] = self.all_domains[key][0]
        return occupation

    def check(self, occupation, message):
        find_solution = self.find_valid_solution(occupation)
        if find_solution:
            occupation = self.add_solution(occupation)
            message["occupation"] = occupation
            nextReceiver = message["ranking"][self.agent_id]["nextSender"]
            if nextReceiver == "end":
                self.send_message(self.coordinator_queue, "confirm", {"sender": self.agent_id,
                                                                      "occupation": occupation})
            else:
                message["sender"] = self.agent_id
                self.send_message(self.connections[nextReceiver], "check", message)
        else:
            message["occupation"] = occupation
            self.backtrack(message)

    def backtrack(self, message):
        message["occupation"] = self.remove_last_solution(message["occupation"])
        message["domains"] = self.all_domains
        self.nogood_list.clear()
        self.selected_values = None
        lastSender = message["ranking"][self.agent_id]["lastSender"]
        message["sender"] = self.agent_id
        self.send_message(lastSender, "nogood", message)
