import multiprocessing
from multiprocessing import Process, Queue, Manager
import time
from sudoku_problem import Sudoku_Problem
from hierarchicalAgents import HA_Coordinator, HierarchicalAttributAgent
from decentralizedAgents import DA_Coordinator, DecentralizedAttributAgent
from constraintAgents import CA_Coordinator, ConstraintAgent
from combinedAgents import ManagerAgent, SolverAgent, C_Coordinator
from datetime import datetime


def new_testseries(agentsystem, size, level, number_of_csp):
    new_test_series = {
        "Testreihe-ID": None,
        "Datum": datetime.now().strftime("%d.%m.%Y"),
        "System": multiprocessing.cpu_count(),
        "Agentsystem": agentsystem,
        "Size": size,
        "Level": level,
        "Anzahl der CSPs": number_of_csp,
        "Gesamt-Initialisierungszeit (ms)": None,
        "Gesamt-Lösungszeit (ms)": None,
        "Gesamtanzahl der Nachrichten": None,
        "Durchschnittliche Lösungszeit (ms)": None,
        "Durchschnittliche Anzahl der Nachrichten": None,
    }
    return new_test_series


def test_combined(ranking_order, sudoku_size, sudoku_lvl, number_of_csp):
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn', force=True)
    agents = []
    if sudoku_size == "9x9":
        n = 9
    elif sudoku_size == "4x4":
        n = 4
    else:
        return
    all_domain_list = list(range(1, n + 1))

    with Manager() as manager:
        problem = Sudoku_Problem(n, n_ary=True, conflict=False)

        connections = dict()
        coordinator_q = manager.Queue()
        solver_q = manager.Queue()
        i = 1
        for constraint in problem.constraints[-n:]:
            connections[i] = manager.Queue()
            i += 1

        coordinator = C_Coordinator(coordinator_queue=coordinator_q,
                                    manager_connections=connections,
                                    solver_connection=solver_q,
                                    level=sudoku_lvl,
                                    sudoku_size=sudoku_size,
                                    rank=ranking_order)
        agents.append(coordinator)

        solver_agent = SolverAgent(agent_id=1,
                                   connections=connections,
                                   constraints=problem.constraints,
                                   order=ranking_order,
                                   coordinator=coordinator_q,
                                   solver_queue=solver_q)
        agents.append(solver_agent)
        i = 1
        for constraint, variables in problem.constraints[-n:]:
            agent = ManagerAgent(agent_id=i,
                                 variables=variables,
                                 connections=connections,
                                 solver=solver_q,
                                 domains=all_domain_list,
                                 coordinator=coordinator_q)
            agents.append(agent)
            i += 1

        for agent in agents:
            agent.start()

        initial_time = (time.perf_counter() * 1000) - start_time

        message = dict()
        message["number_of_csp"] = number_of_csp
        message["test_series"] = new_testseries("combined", sudoku_size, sudoku_lvl, number_of_csp)
        message["initial_time"] = initial_time
        message_data = {"header": "start", "message": message}
        coordinator_q.put(("Start-Main", 0, message_data))

        for agent in agents:
            agent.join()


def test_constraint(ranking_order, sudoku_size, sudoku_lvl, number_of_csp):
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn', force=True)
    agents = []
    if sudoku_size == "9x9":
        n = 9
    elif sudoku_size == "4x4":
        n = 4
    else:
        return
    all_domain_list = list(range(1, n + 1))

    with Manager() as manager:
        problem = Sudoku_Problem(n, n_ary=True, conflict=False)

        connections = dict()
        connections["coordinator"] = manager.Queue()
        i = 1
        for constraint in problem.constraints:
            connections[i] = manager.Queue()
            i += 1

        coordinator = CA_Coordinator(coordinator_queue=connections["coordinator"], connections=connections,
                                     domains=all_domain_list, rank_order=ranking_order, level=sudoku_lvl,
                                     sudoku_size=sudoku_size)
        agents.append(coordinator)

        i = 1
        for constraint, variables in problem.constraints:
            agent = ConstraintAgent(agent_id=i,
                                    variables=variables,
                                    connections=connections,
                                    constraint=constraint)
            agents.append(agent)
            i += 1

        for agent in agents:
            agent.start()

        initial_time = (time.perf_counter() * 1000) - start_time

        message = dict()
        message["number_of_csp"] = number_of_csp
        message["test_series"] = new_testseries("constraint", sudoku_size, sudoku_lvl, number_of_csp)
        message["initial_time"] = initial_time
        message_data = {"header": "start", "message": message}
        connections["coordinator"].put(("Start-Main", 0, message_data))

        for agent in agents:
            agent.join()


def test_decentralized(sudoku_size, sudoku_lvl, number_of_csp):
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn', force=True)
    agents = []
    if sudoku_size == "9x9":
        n = 9
    elif sudoku_size == "4x4":
        n = 4
    else:
        return
    all_domain_list = list(range(1, n + 1))

    with Manager() as manager:
        problem = Sudoku_Problem(n, n_ary=False, conflict=False)

        constraint_dict = {}
        con_dict = {}
        for constraint, variables in problem.constraints:
            for var in variables:
                if var not in constraint_dict:
                    constraint_dict[var] = {}
                    con_dict[var] = {}
                for connected_var in variables:
                    if connected_var != var:
                        constraint_dict[var][connected_var] = constraint
                        con_dict[var][connected_var] = None

        connections = dict()
        connections["coordinator"] = manager.Queue()
        for cell in problem.cells:
            for variable in cell:
                connections[variable] = manager.Queue()

        coordinator = DA_Coordinator(coordinator_queue=connections["coordinator"], connections=connections,
                                     domains=all_domain_list, con_dict=con_dict, level=sudoku_lvl,
                                     sudoku_size=sudoku_size)
        agents.append(coordinator)

        i = 1
        for cell in problem.cells:
            for variable in cell:
                agent = DecentralizedAttributAgent(agent_id=i, name=variable,
                                                   coordinator_queue=connections["coordinator"],
                                                   connections=connections, constraints=constraint_dict[variable])
                agents.append(agent)
                i += 1

        for agent in agents:
            agent.start()

        end_time = time.perf_counter() * 1000
        initial_time = end_time - start_time


        message = dict()
        message["number_of_csp"] = number_of_csp
        message["test_series"] = new_testseries("decentralized", sudoku_size, sudoku_lvl, number_of_csp)
        message["initial_time"] = initial_time
        message_data = {"header": "start", "message": message}
        connections["coordinator"].put(("Start-Main", 0, message_data))

        for agent in agents:
            agent.join()


def test_hierarchy(sudoku_size, sudoku_lvl, number_of_csp):
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn')
    agents = []
    if sudoku_size == "9x9":
        n = 9
    elif sudoku_size == "4x4":
        n = 4
    else:
        return
    all_domain_list = list(range(1, n + 1))

    with Manager() as manager:
        problem = Sudoku_Problem(n, n_ary=False, conflict=False)
        constraint_dict = {}
        con_dict = {}

        for constraint, variables in problem.constraints:
            for var in variables:
                if var not in constraint_dict:
                    constraint_dict[var] = {}
                    con_dict[var] = {}
                for connected_var in variables:
                    if connected_var != var:
                        constraint_dict[var][connected_var] = constraint
                        con_dict[var][connected_var] = None

        connections = dict()
        connections["coordinator"] = manager.Queue()
        for cell in problem.cells:
            for variable in cell:
                connections[variable] = manager.Queue()

        coordinator = HA_Coordinator(connections=connections, domains=all_domain_list, csp_numbers=number_of_csp,
                                     con_dict=con_dict, level=sudoku_lvl, sudoku_size=sudoku_size)
        agents.append(coordinator)

        i = 0
        for cell in problem.cells:
            for variable in cell:
                agent = HierarchicalAttributAgent(agent_id=i, name=variable,
                                                  connections=connections, constraints=constraint_dict[variable])
                agents.append(agent)
                i += 1

        for agent in agents:
            agent.start()

        end_time = time.perf_counter() * 1000
        initial_time = end_time - start_time

        message = dict()
        message["number_of_csp"] = number_of_csp
        message["test_series"] = new_testseries("hierarchical", sudoku_size, sudoku_lvl, number_of_csp)
        message["initial_time"] = initial_time
        message_data = {"header": "start", "message": message}
        time.sleep(3)
        connections["coordinator"].put(("Start-Main", 0, message_data))

        for agent in agents:
            agent.join()


def get_valid_input(prompt, valid_options):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input in valid_options:
            return user_input
        print(f"Ungültige Eingabe. Gültige Optionen sind: {', '.join(valid_options)}")


def get_valid_int_input(prompt, min_value, max_value):
    while True:
        try:
            user_input = int(input(prompt).strip())
            if min_value <= user_input <= max_value:
                return user_input
            print(f"Ungültige Eingabe. Bitte geben Sie eine Zahl zwischen {min_value} und {max_value} ein.")
        except ValueError:
            print(f"Ungültige Eingabe. Bitte geben Sie eine Zahl zwischen {min_value} und {max_value} ein.")


if __name__ == "__main__":
    system_choice = get_valid_input("Wählen Sie das Agentsystem (constraint, decentralized, hierarchy, combined): ",
                                    ["constraint", "decentralized", "hierarchy", "combined"])
    sudoku_size = get_valid_input("Wählen Sie die Größe (9x9 oder 4x4): ", ["9x9", "4x4"])

    if sudoku_size == "4x4":
        number_of_csp = get_valid_int_input("Wählen Sie die Anzahl der CSPs (1 bis 10): ",
                                            1, 10)
        sudoku_lvl = 1

    elif sudoku_size == "9x9":
        sudoku_lvl = get_valid_int_input("Wählen Sie den Schwierigkeitsgrad (1 bis 5): ",
                                         1, 5)
        number_of_csp = get_valid_int_input("Wählen Sie die Anzahl der CSPs (1 bis 100): ",
                                            1, 100)

    if system_choice == "constraint":
        ranking_order = get_valid_input("Geben Sie die Rangfolge an (asc, desc oder random): ",
                                        ["asc", "desc", "random"])
        test_constraint(ranking_order, sudoku_size, sudoku_lvl, number_of_csp)
    elif system_choice == "decentralized":
        test_decentralized(sudoku_size, sudoku_lvl, number_of_csp)
    elif system_choice == "hierarchy":
        test_hierarchy(sudoku_size, sudoku_lvl, number_of_csp)
    elif system_choice == "combined":
        ranking_order = get_valid_input("Geben Sie die Rangfolge an (asc, desc oder random): ",
                                        ["asc", "desc", "random"])
        test_combined(ranking_order, sudoku_size, sudoku_lvl, number_of_csp)
    else:
        print("Ungültiges Agentsystem ausgewählt.")
