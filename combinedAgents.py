from multiprocessing import Process
import random
import itertools
import time
from sudoku_generator import read_sudoku

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
    def __init__(self, agent_id, connections, *args, **kwargs):
        super(SolverAgent, self).__init__()
        self.running = True
        self.name = f"Agent-{agent_id}-Solver"
        self.agent_id = agent_id
        self.connections = connections
        self.own_queue = self.connections[self.agent_id]

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
    def __init__(self, agent_id, connections, variables, domains, *args, **kwargs):
        super(ManagerAgent, self).__init__()
        self.running = True
        self.name = f"Agent-{agent_id}-Manager"
        self.agent_id = agent_id
        self.connections = connections
        self.own_queue = self.connections[self.agent_id]
        self.all_domains = {variable: [None] for variable in variables}
        self.all_domain_list = domains
        self.all_solutions = list(itertools.permutations(self.all_domain_list))

        self.csp_number = 0

        self.occupation = None
        self.possibilities = 1
        self.selected_values = None
        self.combinations = None

        self.message_handlers = {
            "domain_propagation": self.handle_domain_propagation,
            "backtrack": self.handle_backtrack,
            "kill": self.handle_kill,
            "startagent": self.handle_startagent,
            "ask_possibilities": self.handle_ask_possibilities,
            "forward_check": self.handle_forward_check,
            "good_forward_check": self.handle_good_forward_check,
            "bad_forward_check": self.handle_bad_forward_check,
            "ask_data": self.handle_data_collection
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

    def domain_propagation(self):
        keys = list(self.all_domains.keys())
        for key in keys:
            if self.occupation[key] is not None:
                self.all_domains[key] = [self.occupation[key]]
                

    def handle_kill(self, message):
        self.running = False

    def handle_startagent(self, message):
        self.combinations = self.all_solutions
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
