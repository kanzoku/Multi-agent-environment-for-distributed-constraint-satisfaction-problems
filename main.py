import multiprocessing
from multiprocessing import Process, Queue, Manager
import time
from sudoku_problem import Sudoku_Problem
from hierarchicalAgents import HA_Coordinator, HierarchicalAttributAgent
from decentralizedAgents import DA_Coordinator, DecentralizedAttributAgent
from constraintAgents import CA_Coordinator, ConstraintAgent


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

        message = dict()
        message["number_of_csp"] = number_of_csp
        message_data = {"header": "start", "message": message}
        connections["coordinator"].put(("Start-Main", 0, message_data))
        end_time = time.perf_counter() * 1000
        duration = end_time - start_time
        print("Zeit für die Initialisierung:", duration, "ms")

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
                                     domains=all_domain_list, csp_numbers=number_of_csp, con_dict=con_dict,
                                     level=sudoku_lvl,
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
        duration = end_time - start_time
        print("Zeit für die Initialisierung:", duration, "ms")

        message_data = {"header": "start", "message": ""}
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
        duration = end_time - start_time
        print("Zeit für die Initialisierung:", duration, "ms")

        message = dict()
        message["number_of_csp"] = number_of_csp
        message_data = {"header": "start", "message": message}
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
    cpu_count = multiprocessing.cpu_count()
    print(f"Anzahl der verfügbaren CPUs: {cpu_count}")
    system_choice = get_valid_input("Wählen Sie das Agentsystem (constraint, decentralized, hierarchy): ",
                                    ["constraint", "decentralized", "hierarchy"])
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
    else:
        print("Ungültiges Agentsystem ausgewählt.")
