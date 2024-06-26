import multiprocessing
from multiprocessing import Process, Queue, Manager
import time
from sudoku_problem import Sudoku_Problem
from UnitTest import read_sudoku
from hierarchicalAgents import HA_Coordinator, HierarchicalAttributAgent
from decentralizedAgents import DA_Coordinator, DecentralizedAttributAgent
from constraintAgents import CA_Coordinator, ConstraintAgent


def test_constraint():
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn', force=True)
    agents = []

    with Manager() as manager:
        n = 9
        all_domain_list = list(range(1, n + 1))
        problem = Sudoku_Problem(n, n_ary=True, conflict=False)

        connections = dict()
        connections["coordinator"] = manager.Queue()
        i = 1
        for constraint in problem.constraints:
            connections[i] = manager.Queue()
            i += 1

        coordinator = CA_Coordinator(coordinator_queue=connections["coordinator"], connections=connections,
                                     domains=all_domain_list)
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
        message["number_of_csp"] = 100
        message_data = {"header": "start", "message": message}
        connections["coordinator"].put(("Start-Main", 0, message_data))
        end_time = time.perf_counter() * 1000
        duration = end_time - start_time
        print("Zeit für die Initialisierung:", duration, "ms")

        for agent in agents:
            agent.join()


def test_decentralized():
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn', force=True)
    agents = []
    n = 9
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
                                     domains=all_domain_list, csp_numbers=1, con_dict=con_dict)
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


def test_hierarchy():
    start_time = time.perf_counter() * 1000
    multiprocessing.set_start_method('spawn')
    agents = []
    n = 9
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

        coordinator = HA_Coordinator(connections=connections, domains=all_domain_list, csp_numbers=1, con_dict=con_dict)
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
        message["number_of_csp"] = 2
        message_data = {"header": "start", "message": message}
        connections["coordinator"].put(("Start-Main", 0, message_data))

        for agent in agents:
            agent.join()


if __name__ == "__main__":

    # test_hierarchy()
    # test_decentralized()
    test_constraint()
