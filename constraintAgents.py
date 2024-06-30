from multiprocessing import Process
import random
import itertools
import time
from databank_manager import TestResultsManager


class CA_Coordinator(Process):
    def __init__(self, coordinator_queue, connections, domains, rank_order, level, sudoku_size, *args, **kwargs):
        super(CA_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.connections = connections
        self.domains = domains
        self.rank_order = rank_order
        self.level = level
        self.size = sudoku_size
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = 0
        self.solving_time = 0

        self.data_collection = dict()
        self.all_solution_collection = dict()

        self.prepared_dict = self.prepare_dict()
        self.status_dict = dict()
        self.possibilities = dict()
        self.collected_data = dict()

        self.test_series = None
        self.databank_manager = TestResultsManager("datenbank.xlsx")
        self.test_data_collection = dict()

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "start": self.handle_start,
            "domain_propagation": self.handle_propagation,
            "possible": self.handle_ask_possibilities,
            "ask_data": self.handle_data_collection
        }

    def update_all_solution_collection(self):
        for key in self.data_collection.keys():
            self.all_solution_collection[key] = self.all_solution_collection.get(key, 0) + self.data_collection[key]

    def prepare_dict(self):
        preparation_dict = dict()
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            preparation_dict[connection] = None
        return preparation_dict

    def write_detailed_test_series(self):
        detailed_test_series_data = {"Testreihe-ID": self.test_series["Testreihe-ID"],
                                     "Lösung-ID": self.csp_number,
                                     "System": self.test_series["System"],
                                     "Agentsystem": self.test_series["Agentsystem"],
                                     "Kommentar": self.rank_order,
                                     "Size": self.size,
                                     "Level": self.level,
                                     "Lösungszeit (ms)": round(self.test_data_collection[self.csp_number]["duration"],
                                                               2),
                                     "check": self.data_collection.get("check", 0),
                                     "domain_propagation": self.data_collection.get("domain_propagation", 0),
                                     "backtrack": self.data_collection.get("backtrack", 0),
                                     "backjump": self.data_collection.get("backjump", 0),
                                     "possible": self.data_collection.get("possible", 0),
                                     "forward_check": self.data_collection.get("forward_check", 0),
                                     "good_forward_check": self.data_collection.get("good_forward_check", 0),
                                     "bad_forward_check": self.data_collection.get("bad_forward_check", 0),
                                     "confirm": self.data_collection.get("confirm", 0),
                                     "Wertveränderungen": self.data_collection.get("solution_changed", 0),
                                     "Initialisierungs-Nachrichten": (
                                             self.data_collection.get("domain_propagation", 0) +
                                             self.data_collection.get("possible", 0)),
                                     "Lösungs-Nachrichten": (self.data_collection.get("confirm", 0) +
                                                             self.data_collection.get("forward_check", 0) +
                                                             self.data_collection.get("good_forward_check", 0) +
                                                             self.data_collection.get("bad_forward_check", 0) +
                                                             self.data_collection.get("backtrack", 0) +
                                                             self.data_collection.get("backjump", 0) +
                                                             self.data_collection.get("check", 0))}
        detailed_test_series_data["Gesamtanzahl der Nachrichten"] = \
            (detailed_test_series_data["Initialisierungs-Nachrichten"] +
             detailed_test_series_data["Lösungs-Nachrichten"])
        self.databank_manager.add_detailed_test_series(detailed_test_series_data)
        self.test_data_collection["Gesamtanzahl der Nachrichten"] = (
                self.test_data_collection.get("Gesamtanzahl der Nachrichten", 0) +
                detailed_test_series_data["Gesamtanzahl der Nachrichten"])

    def write_test_series(self):
        self.test_series["Gesamt-Lösungszeit (ms)"] = round(self.test_data_collection.get("solution_time", 0), 2)
        self.test_series["Gesamtanzahl der Nachrichten"] = self.test_data_collection.get("Gesamtanzahl der Nachrichten",
                                                                                         0)
        self.test_series["Durchschnittliche Lösungszeit (ms)"] = round(
            self.test_series["Gesamt-Lösungszeit (ms)"] / self.test_data_collection["solution_count"], 2)
        self.test_series["Durchschnittliche Anzahl der Nachrichten"] = round(
            self.test_series["Gesamtanzahl der Nachrichten"] / self.test_data_collection["solution_count"], 2)
        self.databank_manager.add_test_series(self.test_series)

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
            self.test_data_collection["solution_time"] = self.test_data_collection.get("solution_time", 0) + duration
            self.test_data_collection["solution_count"] = self.test_data_collection.get("solution_count", 0) + 1
            self.test_data_collection[self.csp_number] = {"duration": duration, "solution": message["occupation"]}
            self.ask_data()

    def handle_data_collection(self, message):
        for key in message.keys():
            if key == "sender":
                continue
            self.data_collection[key] = self.data_collection.get(key, 0) + message[key]
        self.collected_data[message["sender"]] = True
        if all(self.collected_data.values()):
            print(f"Die Daten des CSP: {self.data_collection}")
            self.test_data_collection[self.csp_number]["messages"] = self.data_collection
            self.write_detailed_test_series()
            self.next_csp()

    def handle_start(self, message):
        print("Starting coordinator")
        self.number_of_csp = int(message["number_of_csp"])
        self.test_series = message["test_series"]
        self.test_series["Testreihe-ID"] = self.databank_manager.get_next_test_series_id()

        initial_time = message["initial_time"]
        self.test_series["Gesamt-Initialisierungszeit (ms)"] = round(initial_time, 2)
        print(f"Initialisierungszeit: {self.test_series['Gesamt-Initialisierungszeit (ms)']} ms")

        self.next_csp()

    def handle_propagation(self, message):
        if int(message["sender"]) in self.status_dict:
            self.status_dict[message["sender"]] = True
            if all(self.status_dict.values()):
                self.all_propagations_true()

    def handle_ask_possibilities(self, message):
        if int(message["sender"]) in self.possibilities:
            self.possibilities[message["sender"]] = message["possibilities"]
            if None not in self.possibilities.values():
                self.solve()

    def ask_data(self):
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            self.send_message(self.connections[connection], "ask_data", {"sender": self.name})

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.update_all_solution_collection()
            self.data_collection = dict()
            self.occupation = self.databank_manager.read_sudoku(number=self.csp_number + 1,
                                                                size=self.size, level=self.level)
            self.status_dict = self.prepared_dict.copy()
            self.possibilities = self.prepared_dict.copy()
            self.collected_data = self.prepared_dict.copy()
            self.solving_time = time.perf_counter() * 1000
            for connection in self.connections.keys():
                if connection == "coordinator":
                    continue
                message = {"domains": self.domains, "occupation": self.occupation,
                           "csp_number": self.csp_number + 1}
                self.send_message(self.connections[connection], "startagent", message)
            self.csp_number += 1
        else:

            for connection in self.connections.keys():
                self.send_message(self.connections[connection], "kill", {"sender": self.name})
            print("All CSPs solved")
            self.update_all_solution_collection()
            print(f"Die Daten aller CSPs: {self.all_solution_collection}")
            self.write_test_series()
            self.databank_manager.save_dataframes()
            self.running = False

    def all_propagations_true(self):
        for connection in self.connections.keys():
            if connection == "coordinator":
                continue
            self.send_message(self.connections[connection], "ask_possibilities", {"sender": self.name})
        pass

    def solve(self):
        print("Solving")
        ranking, start = self.sort_and_create_sender_dict(self.possibilities, self.rank_order)
        # print(ranking)
        if start is not None:
            self.send_message(self.connections[start], "start_solve", {"sender": self.name,
                                                                       "ranking": ranking,
                                                                       "occupation": self.occupation})
        else:
            print("No start found")

    def sort_and_create_sender_dict(self, data, order='asc'):
        # print(data)
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
        self.backjump_condition = True
        self.data_collection_dict = None

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "check": self.handle_check,
            "domain_propagation": self.handle_domain_propagation,
            "backtrack": self.handle_backtrack,
            "backjump": self.handle_backjump,
            "kill": self.handle_stop,
            "startagent": self.handle_startagent,
            "ask_possibilities": self.handle_ask_possibilities,
            "start_solve": self.handle_start_solve,
            "forward_check": self.handle_forward_check,
            "good_forward_check": self.handle_good_forward_check,
            "bad_forward_check": self.handle_bad_forward_check,
            "ask_data": self.handle_data_collection
        }

    def prepare_forward_check_dic(self, ranking):
        preparation_dict = dict()
        current_id = ranking[self.agent_id]['nextSender']
        while current_id != 'end':
            next_sender = ranking[current_id]['nextSender']
            preparation_dict[current_id] = False
            current_id = next_sender
        return preparation_dict

    def clear_forward_check_dic(self):
        for key in self.forward_check_dic.keys():
            self.forward_check_dic[key] = False

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        self.data_collection_dict[header] = self.data_collection_dict.get(header, 0) + 1
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
                domain_set.discard(self.occupation[key])

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
            if len(set(combination)) != len(combination):
                continue

            if self.is_blocked_combination(combination, keys):
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
        self.send_message(self.connections["coordinator"], "possible", {"sender": self.agent_id,
                                                                        "possibilities": self.possibilities})

    def handle_check(self, message):
        self.check(message["occupation"], message)

    def handle_data_collection(self, message):
        new_message = self.data_collection_dict.copy()
        new_message["sender"] = self.agent_id
        self.send_message(self.connections["coordinator"], "ask_data", new_message)

    def handle_backtrack(self, message):
        # print(f"Agent {self.agent_id} received backtrack message")
        self.forward_check_filter += 1
        occ_dict = message["occupation"]
        occ_dict = self.add_bad_combination(occ_dict)
        self.check(occ_dict, message)

    def handle_backjump(self, message):
        self.forward_check_filter += 1
        changed = False
        domain_copy = message["domains"]
        for key in domain_copy.keys():
            if key in self.selected_values.keys():
                changed = True
                break
        if changed:
            occ_dict = message["occupation"]
            occ_dict = self.add_bad_combination(occ_dict)
            self.check(occ_dict, message)
        else:

            last_sender = message["ranking"][self.agent_id]["lastSender"]
            if last_sender == "start":
                occ_dict = message["occupation"]
                occ_dict = self.add_bad_combination(occ_dict)
                self.check(occ_dict, message)
            else:
                message_new = message.copy()
                message_new["occupation"] = self.remove_last_solution(message["occupation"])
                self.send_message(self.connections[message["ranking"][self.agent_id]["lastSender"]],
                                  "backtrack", message_new)

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
        self.backjump_condition = True
        self.solution_set = None
        self.selected_values = None
        self.forward_check_dic = None
        self.data_collection_dict = dict()
        self.nogood_list.clear()
        for key in self.all_domains.keys():
            self.all_domains[key] = [None]
        self.occupation = message["occupation"]
        self.csp_number = message["csp_number"]
        self.all_domain_list = message["domains"]
        self.domain_propagation()

    def handle_start_solve(self, message):
        if message["ranking"][self.agent_id]["lastSender"] == "start":
            self.backjump_condition = False
            message["backjump"] = False
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
                self.send_message(self.connections[nextReceiver], "check", message)

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
        self.data_collection_dict["solution_changed"] = self.data_collection_dict.get("solution_changed", 0) + 1
        return occupation

    def remove_last_solution(self, occupation):
        for key in self.selected_values.keys():
            if key not in occupation:
                continue
            if len(self.all_domains[key]) > 1:
                occupation[key] = None
        return occupation

    def check(self, occupation, message):
        # print(f"Agent {self.agent_id} {self.all_domains}")
        if not self.backjump_condition and not message["backjump"]:
            self.backjump_condition = True
            message["backjump"] = True

        find_solution = self.find_valid_solution(occupation)
        if self.forward_check_dic is None:
            self.forward_check_dic = self.prepare_forward_check_dic(message["ranking"])

        if find_solution:
            new_message = message.copy()
            occupation_new = self.add_solution(occupation)
            # print(f"Agent {self.agent_id} found solution: {occupation_new}")
            new_message["occupation"] = occupation_new
            new_message["sender"] = self.agent_id
            new_message["filter"] = self.forward_check_filter
            self.clear_forward_check_dic()
            if not self.forward_check_dic:
                self.send_message(self.connections["coordinator"], "confirm", message)
            else:
                for connection in self.forward_check_dic.keys():
                    self.send_message(self.connections[connection], "forward_check", new_message)

        else:
            if self.backjump_condition:
                self.backjump(message)
            else:
                self.backtrack(message)

    def backjump(self, message):
        lastSender = message["ranking"][self.agent_id]["lastSender"]
        new_message = dict()
        new_message["domains"] = self.all_domains
        new_message["ranking"] = message["ranking"]
        new_message["sender"] = self.agent_id
        new_message["occupation"] = self.remove_last_solution(message["occupation"])
        self.nogood_list.clear()
        self.selected_values = None
        self.send_message(self.connections[int(lastSender)], "backtrack", new_message)

    def backtrack(self, message):
        lastSender = message["ranking"][self.agent_id]["lastSender"]
        new_message = message.copy()
        new_message["ranking"] = message["ranking"]
        new_message["sender"] = self.agent_id
        new_message["occupation"] = self.remove_last_solution(message["occupation"])
        self.nogood_list.clear()
        self.selected_values = None
        if lastSender == "start":
            new_message["backjump"] = False
            self.check(new_message["occupation"], new_message)
        else:
            self.send_message(self.connections[int(lastSender)], "backtrack", new_message)
