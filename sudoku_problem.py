import os
import sys

# Get the current directory and navigate to the parent directory
current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from csp import Constraint_Satisfaction_Problem
from csp_solver import CSP_Solver
import string
import math
import random as rnd


class Sudoku_Problem(Constraint_Satisfaction_Problem):

    def __init__(self, n, n_ary=False, include_task=True, conflict=False):
        self.cells = []
        self.constraints = []
        self.alphabet = list(string.ascii_lowercase)

        if conflict == False:
            self.n = n
        else:
            self.n = 4

        self.create_variables()

        if n_ary == True:
            self.create_n_ary_constraints()
        else:
            self.create_binary_constraints()

        self.create_csp()

        if include_task == True:
            if n == 4:
                self.include_task_n4()

            if n == 9:
                self.include_task_n9()

            if conflict == True:
                self.include_task_n4_conflict()

    def create_variables(self):
        for i in range(0, self.n):
            column = []
            for j in range(0, self.n):
                column.append(str(f"{self.alphabet[i]}{j + 1}"))

            self.cells.append(column)

        self.cellsT = [list(row) for row in zip(*self.cells)]  # Transpose of the cells

    def create_binary_constraints(self):

        # row constraints
        for row in self.cells:
            for i in row:
                for j in row:
                    if i != j:
                        if f"{j} != {i}" not in self.constraints:
                            self.constraints.append((f"{i} != {j}", [i, j]))

        # column constraints
        for row in self.cellsT:
            for i in row:
                for j in row:
                    if i != j:
                        if f"{j} != {i}" not in self.constraints:
                            self.constraints.append((f"{i} != {j}", [i, j]))

        # block constraints
        n = len(self.cells)
        block_size = int(self.n ** 0.5)
        blocks = []
        for i in range(0, self.n, block_size):
            for j in range(0, self.n, block_size):
                block = []
                for k in range(block_size):
                    for l in range(block_size):
                        block.append(self.cells[i + k][j + l])
                blocks.append(block)

        for block in blocks:
            for i in block:
                for j in block:
                    if i != j:
                        if f"{j} != {i}" not in self.constraints:
                            self.constraints.append((f"{i} != {j}", [i, j]))

    def create_csp(self):
        self.csp = Constraint_Satisfaction_Problem()

        for i in self.cells:
            for j in i:
                self.csp.add_domain(f"{j}", list(range(1, self.n + 1)))

        constraint_counter = 0
        for constraint in self.constraints:
            constraint_counter += 1
            self.csp.add_constraint(constraint_counter, constraint[0], constraint[1])  # row

    def create_n_ary_constraints(self):

        target_factorial = 1
        for i in range(1, self.n + 1):
            target_factorial = target_factorial * i

            # row constraints
        for row in self.cells:
            constraint = ""
            for i in row:
                constraint += f"{i} * "

            constraint = constraint[:-3]
            constraint += f" == {target_factorial}"
            self.constraints.append((constraint, row))

        for col in self.cellsT:
            constraint = ""
            for i in col:
                constraint += f"{i} * "

            constraint = constraint[:-3]
            constraint += f" == {target_factorial}"
            self.constraints.append((constraint, col))

        # block constraints
        # n = len(self.cells)
        block_size = int(self.n ** 0.5)
        blocks = []
        for i in range(0, self.n, block_size):
            for j in range(0, self.n, block_size):
                block = []
                for k in range(block_size):
                    for l in range(block_size):
                        block.append(self.cells[i + k][j + l])
                blocks.append(block)

        for block in blocks:
            constraint = ""
            for i in block:
                constraint += f"{i} * "

            constraint = constraint[:-3]
            constraint += f" == {target_factorial}"
            self.constraints.append((constraint, block))

    def create_csp(self):
        self.csp = Constraint_Satisfaction_Problem()
        self.csp.name = "sudoku_problem"
        for i in self.cells:
            for j in i:
                self.csp.add_domain(f"{j}", list(range(1, self.n + 1)))

        constraint_counter = 0
        for constraint in self.constraints:
            constraint_counter += 1
            self.csp.add_constraint(constraint_counter, constraint[0], constraint[1])  # row

    def generate_puzzle(self, num_clues):
        """Generate a Sudoku puzzle with a given number of clues."""

        self.solver = CSP_Solver(self.csp.domains, self.csp.constraints)
        self.solutions = self.solver.solve(max_solutions=1, constraint_propagation="AC-3",
                                           search_algorithm="Backjumping")
        self.full_sudoku = self.solutions[rnd.randint(0, len(self.solutions) - 1)] if self.solutions else {}

        puzzle = self.full_sudoku.copy()
        cells = list(puzzle.keys())
        cells_to_remove = rnd.sample(cells, len(cells) - num_clues + 1)
        for cell in cells_to_remove:
            del puzzle[cell]

        for key in puzzle.keys():
            self.csp.set_domain(key, puzzle[key])

    def visualize_sudoku(self, domains=None):
        """Visualize a Sudoku grid of size n x n in the console."""

        n = int(len(self.csp.domains) ** 0.5)  # Fix here: get the square root of the length of domains

        # Generating rows and columns based on n
        rows = 'abcdefghijklmnopqrstuvwxyz'[:n]
        cols = list(range(1, n + 1))

        # Determine the block size (e.g., for 9x9 Sudoku, block size is 3x3)
        block_size = int(n ** 0.5)

        # Separator for the blocks
        separator = "+" + ("-" * (block_size * 3 + 2)) * block_size + "+"

        for i, row in enumerate(rows):
            if i % block_size == 0:
                print(separator)

            for j in cols:
                if domains == None:
                    domain = self.csp.domains.get(f'{row}{j}', [])
                else:
                    domain = domains.get(f'{row}{j}', [])
                # Check if the domain contains all possible values from 1 to n or is empty
                if domain == list(range(1, n + 1)) or not domain:
                    cell_value = ' '
                else:
                    # Using the first value in the domain for visualization

                    cell_value = domain[0]

                if j % block_size == 1:
                    print("|", end=" ")
                print(str(cell_value).rjust(2), end=" ")
                if j % n == 0:
                    print("|")
        print(separator)

    def include_task_n4(self):
        self.csp.domains["a4"] = [2]
        self.csp.domains["b1"] = [1]
        self.csp.domains["b3"] = [4]
        self.csp.domains["c1"] = [4]
        self.csp.domains["d3"] = [3]

    def include_task_n9(self):
        self.csp.domains["a1"] = [4]
        self.csp.domains["a2"] = [1]
        self.csp.domains["a4"] = [8]
        self.csp.domains["a5"] = [6]
        self.csp.domains["a6"] = [5]
        self.csp.domains["a9"] = [7]
        self.csp.domains["b2"] = [5]
        self.csp.domains["b4"] = [2]
        self.csp.domains["b3"] = [6]
        self.csp.domains["b6"] = [7]
        self.csp.domains["b7"] = [4]
        self.csp.domains["b8"] = [8]
        self.csp.domains["c1"] = [2]
        self.csp.domains["c3"] = [7]
        self.csp.domains["c4"] = [4]
        self.csp.domains["c5"] = [9]
        self.csp.domains["c7"] = [5]
        self.csp.domains["c9"] = [6]
        self.csp.domains["d2"] = [6]
        self.csp.domains["d5"] = [7]
        self.csp.domains["d7"] = [1]
        self.csp.domains["d8"] = [5]
        self.csp.domains["e1"] = [3]
        self.csp.domains["e3"] = [1]
        self.csp.domains["e4"] = [5]
        self.csp.domains["e6"] = [6]
        self.csp.domains["e8"] = [7]
        self.csp.domains["e9"] = [2]
        self.csp.domains["f2"] = [9]
        self.csp.domains["f3"] = [5]
        self.csp.domains["f5"] = [4]
        self.csp.domains["f6"] = [2]
        self.csp.domains["f7"] = [3]
        self.csp.domains["f9"] = [8]
        self.csp.domains["g1"] = [1]
        self.csp.domains["g3"] = [8]
        self.csp.domains["g4"] = [6]
        self.csp.domains["g8"] = [2]
        self.csp.domains["g9"] = [9]
        self.csp.domains["h1"] = [5]
        self.csp.domains["h2"] = [2]
        self.csp.domains["h5"] = [1]
        self.csp.domains["h6"] = [8]
        self.csp.domains["h7"] = [6]
        self.csp.domains["h8"] = [4]
        self.csp.domains["i1"] = [6]
        self.csp.domains["i4"] = [3]
        self.csp.domains["i5"] = [2]
        self.csp.domains["i8"] = [1]
        self.csp.domains["i9"] = [5]

    def include_task_n4_conflict(self):
        self.csp.domains["b1"] = [1]
        self.csp.domains["b2"] = [2]
        self.csp.domains["b3"] = [3]
        self.csp.domains["b4"] = [4]
        self.csp.domains["a1"] = [4]
        self.csp.domains["a2"] = [3]
        self.csp.domains["a3"] = [1]
        self.csp.domains["a4"] = [2]
        self.csp.domains["c1"] = [3]
        self.csp.domains["c2"] = [1]
        self.csp.domains["c3"] = [4]
        self.csp.domains["c4"] = [2]
        self.csp.domains["d1"] = [2]
        self.csp.domains["d2"] = [4]
        self.csp.domains["d3"] = [1]
        self.csp.domains["d4"] = [3]

# problem = Sudoku_Problem(4, n_ary = False, conflict = True)

# for i in list(range(0,len(problem.csp.constraints))):
#    if [element for element in ["a3", "a4"] if element in problem.csp.constraints[i].variables]:
#        problem.csp.constraints[i].type = "soft"
#        problem.csp.constraints[i].costs = 1000

# from csp_conflict_solver import CSP_Consflict_Solver

# Start conflict solving
# problem.csp.define_input_variables(["c3", "c4", "d3", "d4"])
# conflict_solver = CSP_Consflict_Solver(problem.csp, conflict_solving_strategy="resource-related", opening_size = 10)

# problem.csp.constraints[0].variables
# Dual_Encoding_CSP(problem).solve_binary_csp()
# problem.generate_puzzle(30)
# problem.visualize_sudoku()
