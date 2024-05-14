import multiprocessing
from multiprocessing import Process, Queue, Manager
from loguru import logger
from sudoku_problem import Sudoku_Problem
import time
import json
from UnitTest import read_sudoku
from hierarchicalAgents import HierarchicalAttributAgent


def setup_logger():
    config = {
        "handlers": [
            {"sink": "file.log", "enqueue": True, "level": "INFO"},
        ],
    }
    logger.configure(**config)




if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    setup_logger()
    log_queue = Queue()
    # TODO Initialisierung der Agenten und des Sodoku-Problems und Start-Message an den ersten Agenten senden
    with Manager() as manager:
        n = 9
        all_domain_list = list(range(1, n + 1))
        problem = Sudoku_Problem(n, n_ary=False, conflict=False)
        #print(problem.constraints)
        constraint_dict = {}
        con_dict = {}
        occupation_dict = {}
        for constraint, variables in problem.constraints:
            for var in variables:
                if var not in constraint_dict:
                    constraint_dict[var] = {}
                    con_dict[var] = {}
                    occupation_dict[var] = None
                for connected_var in variables:
                    if connected_var != var:
                        constraint_dict[var][connected_var] = constraint
                        con_dict[var][connected_var] = None

        # import pprint

        occupation_dict = read_sudoku(1)

        for key in con_dict:
            for key2 in con_dict[key]:
                if key2 in occupation_dict and not occupation_dict[key2] is None:
                    con_dict[key][key2] = occupation_dict[key2]
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(con_dict)
        connections = dict()
        for cell in problem.cells:
            for variable in cell:
                connections[variable] = manager.Queue()
        agents = []
        i = 0
        for cell in problem.cells:
            for variable in cell:
                agent = HierarchicalAttributAgent(agent_id=i, log_queue=log_queue, name=variable,
                                  connections=connections, constraints=constraint_dict[variable],
                                  all_domains=all_domain_list, n=n*n, occupation=con_dict[variable])
                agents.append(agent)
                i += 1

        # pp.pprint(constraint_dict)
        for agent in agents:
            agent.start()

        # for agent in agents:
        #     if occupation_dict[agent.name] is not None:
        #         agent.send_message(agent.task_queue, "startagent", {"identifier": [],
        #                                                         "sender": [], "occupation": occupation_dict})
        agents[7].send_message(agents[0].task_queue, "startagent", {"identifier": [],
                                                                    "sender": [], "occupation": occupation_dict})
        # print(f"Start {time.time()}")
        # #for agent in agents:
        # #    agent.send_message(agent.task_queue, "kill", {"kill": ""})
        #
        log_queue.close()
        for agent in agents:
            agent.join()
    # problem = Sudoku_Problem(9, n_ary=True, conflict=False)
    # for constraint in problem.constraints:
    #     print(constraint)

