import json
from multiprocessing import Process
import random
import itertools
import time
from UnitTest import read_sudoku


class CA_Coordinator(Process):
    def __init__(self, coordinator_queue, connections, domains, *args, **kwargs):
        super(CA_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.connections = connections
        self.domains = domains
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = 0
        self.solving_time = 0

        self.prepared_dict = self.prepare_dict()
        self.status_dict = dict()
        self.possibilities = dict()

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "start": self.handle_start,
            "domain_propagation": self.handle_propagation,
            "possible": self.handle_ask_possibilities
        }

    def prepare_dict(self):
        preparation_dict = dict()
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            preparation_dict[connection] = None
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

    def handle_confirm(self, message):
        if all([value is not None for value in message["occupation"].values()]):
            print(f"Solution found: {message['occupation']}")
            end_time = time.perf_counter() * 1000
            duration = end_time - self.solving_time
            print("Zeit für die Lösung:", duration, "ms")
            self.next_csp()

    def handle_start(self, message):
        print("Starting coordinator")
        self.number_of_csp = int(message["number_of_csp"])
        self.next_csp()

    def handle_propagation(self, message):
        if int(message["sender"]) in self.status_dict:
            self.status_dict[message["sender"]] = True
            if all(self.status_dict.values()):
                print("All propagations received")
                self.all_propagations_true()

    def handle_ask_possibilities(self, message):
        if int(message["sender"]) in self.possibilities:
            self.possibilities[message["sender"]] = message["possibilities"]
            if None not in self.possibilities.values():
                # print("All possibilities received")
                # print(self.possibilities)
                self.solve()

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.occupation = read_sudoku(self.csp_number + 2)
            self.status_dict = self.prepared_dict.copy()
            self.possibilities = self.prepared_dict.copy()
            self.solving_time = time.perf_counter() * 1000
            # self.occupation = {'a1': 2, 'a2': None, 'a3': None, 'a4': 1, 'b1': None, 'b2': 3, 'b3': None, 'b4': None,
            #                    'c1': None, 'c2': None, 'c3': 4, 'c4': None, 'd1': None, 'd2': None, 'd3': None, 'd4': None}
            for connection in self.connections.keys():
                if connection == "coordinator":
                    continue
                message = {"domains": self.domains, "occupation": self.occupation,
                           "csp_number": self.csp_number + 1}
                self.send_message(self.connections[connection], "startagent", message)
            self.csp_number += 1
        else:
            print("All CSPs solved")
            for connection in self.connections.keys():
                self.send_message(self.connections[connection], "kill", {"sender": self.name})
            self.running = False

    def all_propagations_true(self):
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            self.send_message(self.connections[connection], "ask_possibilities", {"sender": self.name})
        pass

    def solve(self):
        print("Solving")
        ranking, start = self.sort_and_create_sender_dict(self.possibilities)
        print(ranking)
        if start is not None:
            self.send_message(self.connections[start], "start_solve", {"sender": self.name,
                                                                 "ranking": ranking, "occupation": self.occupation})
        else:
            print("No start found")

    def sort_and_create_sender_dict(self, data, order='asc'):
        print(data)
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
                    self.receive_message(message["header"], message["message"])

class ConstraintAgent(Process):
    def __init__(self, agent_id, variables, connections, constraint, *args, **kwargs):
        super(ConstraintAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten zur Prioritätsermittlung
        self.task_queue = connections[self.agent_id]  # Queue für Aufgaben
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraint = constraint  # String mit den Constraint des Agenten
        self.all_domains = {variable: [None] for variable in variables}  # Dictionary
        self.all_domain_list = None
        self.possibilities = 1
        self.nogood_list = list()  # Liste mit No-goods des Agenten die eine Kombination blockieren
        self.occupation = None  # Dictionary mit den belegten Domains des Agenten
        self.running = True  # Flag, um den Agenten zu stoppen
        self.selected_values = None  # Ausgewählter Wert des Agenten
        self.csp_number = 0  # Kennung des gerade bearbeitenden CSP
        self.forward_check_filter = 0
        self.forward_check_dic = None

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "check": self.handle_check,
            "domain_propagation": self.handle_domain_propagation,
            "backtrack": self.handle_backtrack,
            "kill": self.handle_stop,
            "startagent": self.handle_startagent,
            "ask_possibilities": self.handle_ask_possibilities,
            "start_solve": self.handle_start_solve,
            "forward_check": self.handle_forward_check,
            "good_forward_check": self.handle_good_forward_check,
            "bad_forward_check": self.handle_bad_forward_check
        }

    def prepare_forward_check_dic(self):
        preparation_dict = dict()
        for connection in self.connections.keys():
            if connection == "coordinator" or connection == self.agent_id:
                continue
            preparation_dict[int(connection)] = False
        return preparation_dict

    def clear_forward_check_dic(self):
        for key in self.forward_check_dic.keys():
            self.forward_check_dic[key] = False

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = {"header": header, "message": message}
        recipient_queue.put((str(self.agent_id), self.csp_number, message_data))

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
            if self.all_domains[key][0] is None:
                self.all_domains[key] = domain_list

        for connection in self.connections.keys():
            if connection != self.agent_id and connection != "coordinator":
                message = {"domains": self.all_domains}
                self.send_message(self.connections[connection], "domain_propagation", message)

        self.send_message(self.connections["coordinator"], "domain_propagation", {"sender": self.agent_id})

    def find_valid_solution(self, occupation, changeDic=False):
        copy_all_domains = self.all_domains.copy()
        for key in copy_all_domains.keys():
            if occupation[key] is not None:
                copy_all_domains[key] = [occupation[key]]

            if len(copy_all_domains[key]) == 0:
                return False

        if changeDic:
            if not self.compare_dictionaries(copy_all_domains, self.all_domains):
                solution = self.solver(copy_all_domains)
                if solution:
                    return True
                else:
                    return False
            return True
        else:
            solution = self.solver(copy_all_domains)
            if solution:
                new_solution_dict = dict()
                for key in solution.keys():
                    if occupation[key] is None:
                        new_solution_dict[key] = solution[key]
                self.selected_values = new_solution_dict
                return True
            else:
                return False

    def solver(self, domain_dict):
        keys = list(domain_dict.keys())
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

    def compare_dictionaries(self, dict1, dict2):
        if dict1.keys() != dict2.keys():
            return False
        for key in dict1:
            if isinstance(dict1[key], list) and isinstance(dict2[key], list):
                if set(dict1[key]) != set(dict2[key]):
                    return False
            else:
                if dict1[key] != dict2[key]:
                    return False
        return True

    def handle_domain_propagation(self, message):
        possibilities = 1

        for key in message["domains"].keys():
            if key in self.all_domains.keys():
                self.all_domains[key] = list(set(self.all_domains[key]) & set(message["domains"][key]))

        for key in self.all_domains.keys():
            possibilities *= len(self.all_domains[key])

        self.possibilities = possibilities

    def handle_ask_possibilities(self, message):
        # print(f"Agent {self.agent_id} mit {self.constraint} und den Domains {self.all_domains}")
        self.send_message(self.connections["coordinator"], "possible", {"sender": self.agent_id,
                                                              "possibilities": self.possibilities})

    def handle_check(self, message):
        self.check(message["occupation"], message)

    def handle_backtrack(self, message):
        # print(f"Agent {self.agent_id} received backtrack message")
        self.forward_check_filter += 1
        occ_dict = message["occupation"]
        occ_dict = self.add_bad_combination(occ_dict)
        self.check(occ_dict, message)


    def add_bad_combination(self, occupation):
        nogood_combination = dict()
        for key in self.selected_values.keys():
            nogood_combination[key] = occupation[key]
            if len(self.all_domains[key]) > 1:
                occupation[key] = None
        self.nogood_list.append(nogood_combination)
        return occupation

    def handle_stop(self, message):
        self.running = False

    def handle_startagent(self, message):
        self.forward_check_filter = 0
        self.forward_check_dic = self.prepare_forward_check_dic()
        self.selected_values = None  # Ausgewählter Wert des Agenten
        self.nogood_list.clear()
        for key in self.all_domains.keys():
            self.all_domains[key] = [None]
        self.occupation = message["occupation"]
        self.csp_number = message["csp_number"]
        self.all_domain_list = message["domains"]
        self.domain_propagation()
        # print(f"Agent {self.agent_id} started with propagation")

    def handle_start_solve(self, message):
        if message["ranking"][self.agent_id]["lastSender"] == "start":
            self.check(self.occupation, message)
        else:
            self.send_message(self.connections["coordinator"], "error_start", {"sender": self.agent_id})

    def handle_forward_check(self, message):
        if self.find_valid_solution(message["occupation"], changeDic=True):
            receiver = int(message["sender"])
            message["sender"] = self.agent_id
            self.send_message(self.connections[receiver], "good_forward_check", message)
        else:
            receiver = int(message["sender"])
            message["sender"] = self.agent_id
            self.send_message(self.connections[receiver], "bad_forward_check", message)

    def handle_good_forward_check(self, message):
        if int(message["filter"]) == self.forward_check_filter:
            self.forward_check_dic[int(message["sender"])] = True
            if all(self.forward_check_dic.values()):
                # print(f"Agent {self.agent_id} received good forward check message")
                nextReceiver = message["ranking"][self.agent_id]["nextSender"]
                message["sender"] = self.agent_id
                if nextReceiver == "end":
                    self.send_message(self.connections["coordinator"], "confirm", message)
                else:
                    self.send_message(self.connections[nextReceiver], "check", message)
                    # print(
                    #     f"Agent {self.agent_id} sent check message to {int(nextReceiver)} with occupation"
                    #     f" {message['occupation']}")

    def handle_bad_forward_check(self, message):
        if int(message["filter"]) == self.forward_check_filter:
            # print(f"Agent {self.agent_id} received bad forward check message")
            self.clear_forward_check_dic()
            self.forward_check_filter += 1
            self.nogood_list.append(self.selected_values)
            new_occ = self.add_bad_combination(message["occupation"])
            self.check(new_occ, message)

    def add_solution(self, occupation):
        for key in self.selected_values.keys():
            if occupation[key] is None:
                occupation[key] = self.selected_values[key]
        return occupation

    def remove_last_solution(self, occupation):
        for key in self.selected_values.keys():
            if key not in occupation:
                continue
            if len(self.all_domains[key]) > 1:
                occupation[key] = None
        return occupation

    def check(self, occupation, message):
        find_solution = self.find_valid_solution(occupation)
        if find_solution:
            new_message = message.copy()
            # print(f"Agent {self.agent_id} found solution: {self.selected_values}")
            occupation_new = self.add_solution(occupation)
            new_message["occupation"] = occupation_new
            new_message["sender"] = self.agent_id
            new_message["filter"] = self.forward_check_filter
            self.clear_forward_check_dic()
            for connection in self.connections.keys():
                if connection != self.agent_id and connection != "coordinator":
                    self.send_message(self.connections[connection], "forward_check", new_message)

        else:
            self.backtrack(message)

    def backtrack(self, message):
        new_message = dict()
        new_message["domains"] = self.all_domains
        new_message["ranking"] = message["ranking"]
        new_message["sender"] = self.agent_id
        new_message["occupation"] = self.remove_last_solution(message["occupation"])
        self.nogood_list.clear()
        self.selected_values = None
        lastSender = message["ranking"][self.agent_id]["lastSender"]
        # print(f"Agent {self.agent_id} sent backtrack message to {int(lastSender)}")
        self.send_message(self.connections[int(lastSender)], "backtrack", new_message)
