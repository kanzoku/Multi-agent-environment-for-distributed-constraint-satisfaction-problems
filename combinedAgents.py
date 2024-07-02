from multiprocessing import Process
import random
import copy
import itertools
import time


class C_Coordinator(Process):
    def __init__(self, coordinator_queue, connections, domains, *args, **kwargs):
        super(C_Coordinator, self).__init__()
        self.name = "coordinator"
        self.coordinator_queue = coordinator_queue
        self.connections = connections
        self.domains = domains
        self.running = True
        self.occupation = None
        self.csp_number = 0
        self.number_of_csp = 0
        self.solving_time = 0

        # Dictionary mit den Funktionen zur Behandlung von Nachrichten
        self.message_handlers = {
            "confirm": self.handle_confirm,
            "start": self.handle_start,
            "domain_propagation": self.handle_propagation,
            "possible": self.handle_ask_possibilities
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

    def next_csp(self):
        if self.csp_number < self.number_of_csp:
            self.occupation = read_sudoku(self.csp_number + 1)
            self.solving_time = time.perf_counter() * 1000
            # self.occupation = {'a1': 2, 'a2': None, 'a3': None, 'a4': 1,
            #                    'b1': None, 'b2': 3, 'b3': None, 'b4': None,
            #                    'c1': None, 'c2': None, 'c3': 4, 'c4': None,
            #                    'd1': None, 'd2': None, 'd3': None, 'd4': None}
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


class SolverAgent(Process):
    def __init__(self, agent_id, connections, constraints, *args, **kwargs):
        super(SolverAgent, self).__init__()
        self.running = True
        self.name = f"Agent-{agent_id}-Solver"
        self.agent_id = agent_id
        self.connections = connections
        self.own_queue = self.connections[self.agent_id]
        self.constraints = constraints

        self.message_handlers = {
            "solve": self.handle_solve,
            "kill": self.handle_kill
        }

    def send_message(self, recipient_queue, header, message):
        # Sendet Nachrichten an andere Agenten
        message_data = {"header": header, "message": message}
        recipient_queue.put((self.name, message["csp_id"], message_data))

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
                    return False
        return True

    def handle_solve(self, message):
        expr_copy = message["constraint"]
        variables = message["variables"].copy()
        for key, value in variables:
            expr_copy = expr_copy.replace(key, str(value))
        try:
            result = eval(expr_copy)
            if result:
                pass
        except Exception as e:
            print(f"Error in {self.name}: {e}")

    def handle_kill(self, message):
        self.running = False

class ManagerAgent(Process):
    def __init__(self, agent_id, connections, solver, variables, domains, *args, **kwargs):
        super(ManagerAgent, self).__init__()
        self.running = True
        self.name = f"Agent-{agent_id}-Manager"
        self.agent_id = agent_id
        self.connections = connections
        self.solver_queue = solver
        self.own_queue = self.connections[self.agent_id]
        self.all_domains = {variable: [] for variable in variables}
        self.row_col_dict = self.create_row_col_dict(variables)
        self.all_domain_list = domains

        self.csp_number = 0

        self.combinations = None
        self.nogood_list = []
        self.selected_values = None

        self.data_collection_dict = dict()

        self.message_handlers = {
            "not_allowed": self.handle_not_allowed,
            "backtrack": self.handle_backtrack,
            "kill": self.handle_kill,
            "startagent": self.handle_startagent,
            "ask_possibilities": self.handle_ask_possibilities,
            "forward_check": self.handle_forward_check,
            "ask_data": self.handle_data_collection
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
        if len(coord) != 2:
            raise ValueError("Invalid coordinate format. Must be a letter followed by a digit.")

        column = coord[0]
        row = coord[1]

        if not column.isalpha() or not row.isdigit():
            raise ValueError("Invalid coordinate format. Must be a letter followed by a digit.")

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

    def send_not_allowed(self, key, value):
        for connection in self.connections.keys():
            message = {"variable": key, "value": value}
            self.send_message(self.connections[connection], "not_allowed", message)

    def is_blocked_combination(self, combination, keys):
        for blocked_condition in self.nogood_list:
            if all(combination[keys.index(k)] == v for k, v in blocked_condition.items()):
                return True
        return False

    def add_occupation(self, selected_values, occupation):
        for key in selected_values.keys():
            occupation[key] = selected_values[key]
        return occupation

    def handle_not_allowed(self, message):
        row, col = self.split_coordinate(message["variable"])
        if row in self.row_col_dict:
            for coord in self.row_col_dict[row]:
                self.all_domains[coord].remove(message["value"])
        if col in self.row_col_dict:
            for coord in self.row_col_dict[col]:
                self.all_domains[coord].remove(message["value"])

    def is_valid_permutation(self, perm, domains):
        keys = list(domains.keys())
        for i, key in enumerate(keys):
            if perm[i] not in domains[key]:
                return False
        return True

    def handle_ask_possibilities(self, message):
        combinations = list(itertools.permutations(self.all_domain_list))
        self.combinations = [comb for comb in combinations if self.is_valid_permutation(comb, self.all_domains)]
        self.send_message(self.solver_queue, "possible", {"possibilities": len(self.combinations)})

    def handle_forward_check(self, message):
        forward_check_dic = copy.deepcopy(self.all_domains)
        selected_values = message["selected_values"]
        for key, value in selected_values.items():
            row, col = self.split_coordinate(key)
            if row in self.row_col_dict:
                for coord in self.row_col_dict[row]:
                    forward_check_dic[coord].remove(value)
            if col in self.row_col_dict:
                for coord in self.row_col_dict[col]:
                    forward_check_dic[coord].remove(value)
        for key in forward_check_dic.keys():
            if len(forward_check_dic[key]) == 0:
                self.send_message(self.connections[message["sender"]], "bad_forward_check",
                                  {"sender": self.agent_id})
                return
        self.send_message(self.solver_queue, "good_forward_check",
                          {"sender": self.agent_id})

    def handle_nogood(self, message):
        self.nogood_list.append(self.selected_values)
        self.handle_check(message)

    def handle_check(self, message):
        key_list = list(self.all_domains.keys())
        for comb in self.combinations:
            if self.is_blocked_combination(comb, key_list):
                continue

            self.data_collection_dict["solution_changed"] = self.data_collection_dict.get("solution_changed", 0) + 1
            self.selected_values = {key_list[i]: comb[i] for i in range(len(key_list))}

            self.send_message(self.solver_queue, "found_solution",
                              {"selected_values": self.selected_values})
            return
        self.send_message(self.solver_queue, "found_no_solution", {"sender": self.name})

    def handle_kill(self, message):
        self.running = False

    def handle_data_collection(self, message):
        new_message = dict()
        new_message["data"] = copy.deepcopy(self.data_collection_dict)
        new_message["sender"] = self.agent_id
        self.send_message(self.connections["coordinator"], "ask_data", new_message)

    def handle_backtrack(self, message):
        self.nogood_list.clear()

    def handle_startagent(self, message):
        self.combinations = None
        self.selected_values = None
        self.data_collection_dict = dict()
        self.nogood_list.clear()
        self.clear_domains()
        self.csp_number = message["csp_number"]
        self.all_domain_list = message["domains"]
        self.domain_propagation(message["occupation"])
