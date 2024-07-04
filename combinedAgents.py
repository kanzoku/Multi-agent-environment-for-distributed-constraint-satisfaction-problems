from multiprocessing import Process
import random
import copy
import itertools
import time
from databank_manager import TestResultsManager


class C_Coordinator(Process):
    def __init__(self, coordinator_queue, manager_connections, solver_connection,
                 level, sudoku_size, rank, *args, **kwargs):
        super(C_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.manager_connections = manager_connections
        self.solver_connection = solver_connection
        self.level = level
        self.size = sudoku_size
        self.rank_order = rank
        self.running = True

        self.csp_number = 0
        self.number_of_csp = 0
        self.solving_time = 0

        self.test_series = None
        self.databank_manager = TestResultsManager("datenbank.xlsx")
        self.test_data_collection = dict()
        self.collected_data = None
        self.data_collection = dict()
        self.all_solution_collection = dict()

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "solved": self.handle_solved,
            "start": self.handle_start,
            "ask_data": self.handle_data_collection,
            "no_solution": self.handle_no_solution,
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
                sender, csp_id, message = self.coordinator_queue.get()
                if csp_id == self.csp_number:
                    self.receive_message(message["header"], message["message"])

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
                                     "not_allowed": self.data_collection.get("not_allowed", 0),
                                     "backtrack": self.data_collection.get("backtrack", 0),
                                     "possible": self.data_collection.get("possible", 0),
                                     "forward_check": self.data_collection.get("forward_check", 0),
                                     "good_forward_check": self.data_collection.get("good_forward_check", 0),
                                     "bad_forward_check": self.data_collection.get("bad_forward_check", 0),
                                     "confirm": self.data_collection.get("solved", 0),
                                     "Wertveränderungen": self.data_collection.get("solution_changed", 0),
                                     "Initialisierungs-Nachrichten": (
                                             self.data_collection.get("domain_propagation", 0) +
                                             self.data_collection.get("possible", 0) +
                                             self.data_collection.get("not_allowed", 0)),
                                     "Lösungs-Nachrichten": (self.data_collection.get("solved", 0) +
                                                             self.data_collection.get("forward_check", 0) +
                                                             self.data_collection.get("good_forward_check", 0) +
                                                             self.data_collection.get("bad_forward_check", 0) +
                                                             self.data_collection.get("backtrack", 0) +
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

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.update_all_solution_collection()
            self.data_collection = dict()
            print("-----------------------------------------")
            occupation = self.databank_manager.read_sudoku(number=self.csp_number + 1, size=self.size, level=self.level)
            if self.csp_number == 0:
                time.sleep(1)
            self.solving_time = time.perf_counter() * 1000
            message = {"occupation": occupation, "csp_number": self.csp_number + 1}
            self.send_message(self.solver_connection, "solve", message)
            self.csp_number += 1
        else:
            print("All CSPs solved")
            for connection in self.manager_connections.keys():
                self.send_message(self.manager_connections[connection], "kill", {"sender": self.name})
            self.send_message(self.solver_connection, "kill", {"sender": self.name})
            self.update_all_solution_collection()
            print(f"Die Daten aller CSPs: {self.all_solution_collection}")
            self.write_test_series()
            self.databank_manager.save_dataframes()
            self.running = False

    def update_all_solution_collection(self):
        for key in self.data_collection.keys():
            self.all_solution_collection[key] = self.all_solution_collection.get(key, 0) + self.data_collection[key]

    def ask_data(self):
        self.collected_data = self.prepare_dict()
        for connection in self.manager_connections.keys():
            self.send_message(self.manager_connections[connection], "ask_data", {"sender": self.name})
        self.send_message(self.solver_connection, "ask_data", {"sender": self.name})

    def prepare_dict(self):
        preparation_dict = dict()
        for connection in self.manager_connections.keys():
            preparation_dict[connection] = None
        preparation_dict["solver"] = None
        return preparation_dict

    def handle_solved(self, message):
        print(f"Solution found: {message['occupation']}")
        duration = time.perf_counter() * 1000 - self.solving_time
        print("Zeit für die Lösung:", duration, "ms")
        self.test_data_collection["solution_time"] = self.test_data_collection.get("solution_time", 0) + duration
        self.test_data_collection["solution_count"] = self.test_data_collection.get("solution_count", 0) + 1
        self.test_data_collection[self.csp_number] = {"duration": duration, "solution": message["occupation"]}
        self.ask_data()

    def handle_no_solution(self, message):
        duration = time.perf_counter() * 1000 - self.solving_time
        print("Zeit:", duration, "ms")
        self.test_data_collection["solution_time"] = self.test_data_collection.get("solution_time", 0) + duration
        self.test_data_collection["solution_count"] = self.test_data_collection.get("solution_count", 0) + 1
        self.test_data_collection[self.csp_number] = {"duration": duration}
        self.ask_data()

    def handle_data_collection(self, message):
        for key in message.keys():
            if key == "sender":
                continue
            self.data_collection[key] = self.data_collection.get(key, 0) + message[key]
        self.collected_data[message["sender"]] = True
        if all(self.collected_data.values()):
            print(f"Die Daten des CSP: {self.data_collection}")
            print("-----------------------------------------")
            print("")
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


class SolverAgent(Process):
    def __init__(self, agent_id, connections, constraints, order, coordinator, solver_queue, *args, **kwargs):
        super(SolverAgent, self).__init__()
        self.running = True
        self.name = f"Agent-{agent_id}-Solver"
        self.agent_id = agent_id
        self.coordinator_queue = coordinator
        self.connections = connections
        self.own_queue = solver_queue
        self.constraints = constraints
        self.order = order

        self.csp_number = 0
        self.data_collection_dict = dict()

        self.occupation = dict()
        self.occupation_key_list = None
        self.status_dict = dict()
        self.possibilities = dict()
        self.ranking_order = None

        self.forward_check_number = 0
        self.forward_check_dict = None
        self.forward_check_sender = None

        self.message_handlers = {
            "solve": self.handle_solve,
            "kill": self.handle_kill,
            "domain_propagation": self.handle_propagation,
            "possible": self.handle_ask_possibilities,
            "check": self.handle_check,
            "bad_forward_check": self.handle_bad_forward_check,
            "good_forward_check": self.handle_good_forward_check,
            "ask_data": self.handle_data_collection,
        }

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
            print(f"{self.name} received unknown message type: {header} with message: {message}")

    def run(self):
        while self.running:
            if not self.own_queue.empty():
                sender, csp_id, message = self.own_queue.get()
                self.receive_message(message["header"], message["message"])

    def solver(self, occupation):
        for constraint, variables in self.constraints:
            if all(occupation[var] is not None for var in variables):
                context = {var: occupation[var] for var in variables}
                if not eval(constraint, {}, context):
                    # print(f"Constraint {constraint} violated with {context}")
                    # print(f"Occupation: {occupation}")
                    return False
        # print(f"All constraints satisfied with {occupation}")
        return True

    def handle_propagation(self, message):
        if int(message["sender"]) in self.status_dict:
            self.status_dict[message["sender"]] = True
            if all(self.status_dict.values()):
                self.all_propagations_true()

    def all_propagations_true(self):
        # print("All propagations received")
        possibilities = dict()
        for connection in self.connections.keys():
            self.send_message(self.connections[connection], "ask_possibilities", {"sender": self.name})
            possibilities[connection] = None
        self.possibilities = possibilities
        self.status_dict = {key: False for key in self.connections.keys()}

    def handle_ask_possibilities(self, message):
        if int(message["sender"]) in self.possibilities:
            self.possibilities[message["sender"]] = message["possibilities"]
            if None not in self.possibilities.values():
                print("Solving")
                self.ranking_order, start = self.sort_and_create_sender_dict(self.possibilities, order=self.order)
                if start is not None:
                    self.send_message(self.connections[start], "check",
                                      {"occupation": self.occupation["start"]})

    def handle_check(self, message):
        sender = message["sender"]
        last_sender = self.ranking_order[sender]["lastSender"]
        next_sender = self.ranking_order[sender]["nextSender"]
        if message["found_solution"]:
            self.occupation[sender] = self.add_selected_values(self.occupation[last_sender], message["selected_values"])
            if self.solver(self.occupation[sender]):
                if next_sender == "end":
                    self.send_message(self.coordinator_queue, "solved",
                                      {"occupation": self.occupation[sender]})
                self.forward_check(sender)
            else:
                self.send_message(self.connections[sender], "nogood", {"selected_values": message["selected_values"]})
        else:
            self.send_message(self.connections[sender], "backtrack", {"sender": self.name})
            if last_sender == "start":
                print("No solution found")
                for key in self.occupation.keys():
                    print(f"{key}: {self.occupation[key]}")
                self.send_message(self.coordinator_queue, "no_solution", {"sender": self.name})
            else:
                self.send_message(self.connections[last_sender], "nogood", {"sender": self.name})

    def forward_check(self, sender):
        self.forward_check_number += 1
        forward_check_dict = dict()
        next_sender = self.ranking_order[sender]["nextSender"]
        while next_sender != "end":
            forward_check_dict[next_sender] = False
            self.send_message(self.connections[next_sender], "forward_check",
                              {"occupation": self.occupation[sender], "check_number": self.forward_check_number})
            next_sender = self.ranking_order[next_sender]["nextSender"]
        self.forward_check_sender = sender
        self.forward_check_dict = forward_check_dict

    def handle_bad_forward_check(self, message):
        if message["check_number"] == self.forward_check_number:
            self.forward_check_number += 1
            self.send_message(self.connections[self.forward_check_sender], "nogood",
                              {"sender": self.name})

    def handle_good_forward_check(self, message):
        if message["check_number"] == self.forward_check_number:
            self.forward_check_dict[message["sender"]] = True
            if all(self.forward_check_dict.values()):
                nextSender = self.ranking_order[self.forward_check_sender]["nextSender"]
                self.send_message(self.connections[nextSender], "check",
                                  {"occupation": self.occupation[self.forward_check_sender]})

    def handle_data_collection(self, message):
        new_message = self.data_collection_dict.copy()
        new_message["sender"] = "solver"
        self.send_message(self.coordinator_queue, "ask_data", new_message)

    def add_selected_values(self, occupation, selected_values):
        new_occupation = occupation.copy()
        for key in selected_values.keys():
            new_occupation[key] = selected_values[key]
        return new_occupation

    def handle_solve(self, message):
        new_message = dict()
        new_message["occupation"] = message["occupation"]
        new_message["csp_number"] = message["csp_number"]
        for connection in self.connections.keys():
            self.send_message(self.connections[connection], "startagent", new_message)
        self.occupation = dict()
        self.csp_number = message["csp_number"]
        self.occupation["start"] = message["occupation"]
        self.forward_check_number = 0
        self.forward_check_dict = None
        self.forward_check_sender = None
        self.status_dict = {key: False for key in self.connections.keys()}

    def handle_kill(self, message):
        self.running = False

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
        self.occupation_key_list = keys

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


class ManagerAgent(Process):
    def __init__(self, agent_id, connections, solver, variables, domains, coordinator, *args, **kwargs):
        super(ManagerAgent, self).__init__()
        self.running = True
        self.name = f"Agent-{agent_id}-Manager"
        self.agent_id = agent_id
        self.connections = connections
        self.solver_queue = solver
        self.coordinator_queue = coordinator
        self.own_queue = self.connections[self.agent_id]
        self.all_domains = {variable: [] for variable in variables}
        self.row_col_dict = self.create_row_col_dict(variables)
        self.all_domain_list = domains
        # print(f"ManagerAgent-{self.agent_id} meine Variablen: {self.all_domains}")
        self.all_solutions = list(itertools.permutations(self.all_domain_list))
        # print(f"ManagerAgent-{self.agent_id} Anzahl der max Lösungen: {len(self.all_solutions)}")

        self.csp_number = 0

        self.combinations = None
        self.nogood_list = []
        self.selected_values = None

        self.adjusted_domains = None

        self.data_collection_dict = dict()

        self.message_handlers = {
            "not_allowed": self.handle_not_allowed,
            "backtrack": self.handle_backtrack,
            "kill": self.handle_kill,
            "startagent": self.handle_startagent,
            "ask_possibilities": self.handle_ask_possibilities,
            "forward_check": self.handle_forward_check,
            "ask_data": self.handle_data_collection,
            "nogood": self.handle_nogood,
            "check": self.handle_check,
        }

    def create_row_col_dict(self, variables):
        row_col_dict = {}

        for coord in variables:
            column, row = self.split_coordinate(coord)

            if row not in row_col_dict:
                row_col_dict[row] = []
            row_col_dict[row].append(coord)

            if column not in row_col_dict:
                row_col_dict[column] = []
            row_col_dict[column].append(coord)

        return row_col_dict

    def split_coordinate(self, coord):
        column = coord[0]
        row = coord[1]
        return column, row

    def clear_domains(self):
        for key in self.all_domains.keys():
            self.all_domains[key] = []

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        self.data_collection_dict[header] = self.data_collection_dict.get(header, 0) + 1
        message_data = {"header": header, "message": message}
        recipient_queue.put((str(self.agent_id), self.csp_number, message_data))

    def receive_message(self, header, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            print(f"{self.name} received unknown message type: {header} with message: {message}")

    def run(self):
        while self.running:
            if not self.own_queue.empty():
                sender, csp_id, message = self.own_queue.get()
                if csp_id == self.csp_number:
                    self.receive_message(message["header"], message["message"])

    def domain_propagation(self, occupation):
        keys = list(self.all_domains.keys())
        domain_set = set(self.all_domain_list)
        for key in keys:
            if occupation[key] is not None:
                self.all_domains[key] = [occupation[key]]
                domain_set.discard(occupation[key])
                self.send_not_allowed(key, occupation[key])

        for key in keys:
            if len(self.all_domains[key]) == 1:
                continue
            self.all_domains[key] = list(domain_set)

        self.send_message(self.solver_queue, "domain_propagation", {"sender": self.agent_id})

    def send_not_allowed(self, key, value):
        for connection in self.connections.keys():
            if connection == self.agent_id:
                continue
            message = {"variable": key, "value": value}
            self.send_message(self.connections[connection], "not_allowed", message)

    def is_blocked_combination(self, combination, keys):
        for blocked_condition in self.nogood_list:
            if all(combination[keys.index(k)] == v for k, v in blocked_condition.items()):
                return True
        return False

    def handle_not_allowed(self, message):
        row, col = self.split_coordinate(message["variable"])
        if row in self.row_col_dict:
            for coord in self.row_col_dict[row]:
                if message["value"] in self.all_domains[coord]:
                    self.all_domains[coord].remove(message["value"])
        if col in self.row_col_dict:
            for coord in self.row_col_dict[col]:
                if message["value"] in self.all_domains[coord]:
                    self.all_domains[coord].remove(message["value"])

    def is_valid_permutation(self, perm, domains):
        keys = list(domains.keys())
        for i, key in enumerate(keys):
            if perm[i] not in domains[key]:
                return False
        return True

    def handle_ask_possibilities(self, message):
        self.combinations = [comb for comb in self.all_solutions if self.is_valid_permutation(comb, self.all_domains)]
        # print(f"Possible combinations: {len(self.combinations)} - {self.agent_id}")
        self.send_message(self.solver_queue, "possible",
                          {"sender": self.agent_id, "possibilities": len(self.combinations)})

    def adjust_domain_occupation(self, forward_check_dic, occupation):
        for key in occupation.keys():
            if occupation[key] is not None:
                if key in forward_check_dic:
                    forward_check_dic[key] = [occupation[key]]
                    continue
                row, col = self.split_coordinate(key)
                if row in self.row_col_dict:
                    for coord in self.row_col_dict[row]:
                        if occupation[key] in forward_check_dic[coord]:
                            forward_check_dic[coord].remove(occupation[key])
                        if len(forward_check_dic[coord]) == 0:
                            return True, forward_check_dic
                if col in self.row_col_dict:
                    for coord in self.row_col_dict[col]:
                        if occupation[key] in forward_check_dic[coord]:
                            forward_check_dic[coord].remove(occupation[key])
                        if len(forward_check_dic[coord]) == 0:
                            return True, forward_check_dic
        # print(f"Adjusting Domain-Dictionary successful {self.agent_id} with Dictionary: {forward_check_dic}")
        return False, forward_check_dic

    def handle_forward_check(self, message):
        check_number = message["check_number"]
        forward_check_dic = copy.deepcopy(self.all_domains)
        trigger, forward_check_dic = self.adjust_domain_occupation(forward_check_dic, message["occupation"])
        if trigger:
            self.send_message(self.solver_queue, "bad_forward_check",
                              {"sender": self.agent_id, "check_number": check_number})
            return
        domain_set = set()
        for key in forward_check_dic.keys():
            if len(forward_check_dic[key]) == 0:
                self.send_message(self.solver_queue, "bad_forward_check",
                                  {"sender": self.agent_id, "check_number": check_number})
                return
            domain_set.update(set(forward_check_dic[key]))
        if len(domain_set) != len(self.all_domain_list):
            self.send_message(self.solver_queue, "bad_forward_check",
                              {"sender": self.agent_id, "check_number": check_number})
        self.send_message(self.solver_queue, "good_forward_check",
                          {"sender": self.agent_id, "check_number": check_number})

    def handle_nogood(self, message):
        self.nogood_list.append(self.selected_values)
        self.handle_check(message)

    def handle_check(self, message):
        key_list = list(self.all_domains.keys())

        if self.adjusted_domains is None:
            domains = copy.deepcopy(self.all_domains)
            trigger_bool, self.adjusted_domains = self.adjust_domain_occupation(domains, message["occupation"])
            if trigger_bool:
                self.send_message(self.solver_queue, "check", {"sender": self.agent_id, "found_solution": False})
                return

        for comb in self.combinations:
            # print(f"Checking combination: {comb} - {self.agent_id}")
            if self.is_blocked_combination(comb, key_list):
                # print("Blocked combination")
                continue

            if not self.is_valid_permutation(comb, self.adjusted_domains):
                # print("Invalid permutation")
                continue

            self.data_collection_dict["solution_changed"] = self.data_collection_dict.get("solution_changed", 0) + 1
            self.selected_values = {key_list[i]: comb[i] for i in range(len(key_list))}
            # print(f"Selected values: {self.selected_values} - {self.agent_id}")
            self.send_message(self.solver_queue, "check",
                              {"selected_values": self.selected_values, "found_solution": True,
                               "sender": self.agent_id})
            return
        self.send_message(self.solver_queue, "check", {"sender": self.agent_id, "found_solution": False})


    def handle_kill(self, message):
        self.running = False

    def handle_data_collection(self, message):
        new_message = self.data_collection_dict.copy()
        new_message["sender"] = self.agent_id
        self.send_message(self.coordinator_queue, "ask_data", new_message)

    def handle_backtrack(self, message):
        self.adjusted_domains = None
        self.nogood_list.clear()

    def handle_startagent(self, message):
        self.combinations = None
        self.adjusted_domains = None
        self.selected_values = None
        self.data_collection_dict = dict()
        self.nogood_list.clear()
        self.clear_domains()
        self.csp_number = message["csp_number"]
        self.domain_propagation(message["occupation"])
