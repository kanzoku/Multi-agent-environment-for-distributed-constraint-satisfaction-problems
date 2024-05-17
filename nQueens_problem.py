import os
import sys

# Get the current directory and navigate to the parent directory
current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from csp import Constraint_Satisfaction_Problem

class N_Queens_Problem(Constraint_Satisfaction_Problem):
    """
    The n-Queens problem is a classic example of a constraint satisfaction problem where the goal is to place n queens on an n×n chessboard such that no two queens threaten each other. This means no two queens can be in the same row, column, or diagonal.
    
    In mathematical formulation, the n-Queens problem can be stated as follows:
    
    Variables:
    Let Q = {Q1, Q2, ..., Qn} be the set of variables, where each variable Qi represents the position of the queen in the i-th row.
    
    Domains:
    The domain of each variable Qi is Di = {1, 2, ..., n}, representing the possible positions (columns) of the queen in the i-th row.
    
    Constraints:
    
        One queen per row: this is enforced by the definition of the variables themselves. Each variable represents one queen in a given row, so there is always only one queen per row.
    
        One queen per column: This is enforced by a constraint that says all variables must have different values. Since the value of a variable represents the column in which the queen is located, this constraint ensures that there is only one queen per column.
    
        One queen per diagonal: This is enforced by two constraints which state that no two queens may lie on the same diagonal. For each pair of variables Qi and Qj (i ≠ j), the following constraints must be satisfied:
                |i - j| ≠ |Qi - Qj| (for the main diagonals).
                i + Qi ≠ j + Qj (for the secondary diagonals).
            
        The constraints can be expressed by the following conditions:
        
            One queen per column: For all i, j ∈ {1, 2, ..., n} with i ≠ j, Qi ≠ Qj must hold. This ensures that no two queens are in the same column.
        
            One queen per diagonal: for all i, j ∈ {1, 2, ..., n} with i ≠ j, the following conditions must hold:
                |i - j| ≠ |Qi - Qj| (for the main diagonals).
                i + Qi ≠ j + Qj (for the secondary diagonals).
        
        These conditions ensure that no two queens are on the same diagonal. Together with the condition "One queen per column", these constraints ensure that no two queens can attack each other.
    
    """
    
    def __init__(self, n = 8):
        # Initialize the base Constraint Satisfaction Problem
        self.csp = Constraint_Satisfaction_Problem()
        self.csp.name = "nQueens_problem"
        self.n = n  # The size of the chessboard (n x n)
        
        # Create domains for each queen
        # Each queen 'qi' can be in any column of the ith row, hence a domain from 1 to n is assigned
        for i in range(1, self.n + 1):
            self.csp.add_domain(f"q{i}", list(range(1, self.n + 1)))
    
        # Create constraints to ensure no two queens threaten each other
        constraint_counter = 0
        for queen1 in range(0, self.n):
            for queen2 in range(0, self.n):
                if queen1 < queen2:  # Avoid redundant comparisons, as each pair is considered only once
                    # Constraint for different columns (no two queens in the same column)
                    constraint_counter += 1
                    self.csp.add_constraint(constraint_counter, f"{list(self.csp.domains.keys())[queen1]} != {list(self.csp.domains.keys())[queen2]}", [list(self.csp.domains.keys())[queen1], list(self.csp.domains.keys())[queen2]])
    
                    # Constraints for diagonals - ensures that no two queens share the same diagonal
                    # For the main diagonals
                    self.csp.add_constraint(constraint_counter, f"{queen1 - queen2} != {list(self.csp.domains.keys())[queen1]} - {list(self.csp.domains.keys())[queen2]}", [list(self.csp.domains.keys())[queen1], list(self.csp.domains.keys())[queen2]])
                    # For the secondary diagonals
                    self.csp.add_constraint(constraint_counter, f"{queen2 - queen1} != {list(self.csp.domains.keys())[queen1]} - {list(self.csp.domains.keys())[queen2]}", [list(self.csp.domains.keys())[queen1], list(self.csp.domains.keys())[queen2]])
    
    def print_solution(self, solution):
        # Print the solution in a readable chessboard format
        for row in range(1, self.n + 1):
            line = ""
            for column in range(0, self.n):
                if list(solution.values())[column] == row:
                    line += "Q "  # Place a queen ('Q') in the position if it matches the solution
                else:
                    line += ". "  # Empty spot
            print(line)
        print("\n")  # New line after printing the board
