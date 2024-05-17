"""
Project Name: CSP solution envioment
Description: This project provides a Python environment that can model and solve constraint satisfaction problem.
Author: Kevin Herrmann
Contact: kevinherrmann95@web.de
License: MIT
Project Status: stable
Required libraries: numpy, networkx, math
Version: 1.0.0
Last Modified: 2023-10-30
Copyright (c) 2023 Kevin Herrmann
"""

import os
import sys

# Get the current directory and navigate to the parent directory
current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from csp import Constraint_Satisfaction_Problem

class Send_More_Money_Problem(Constraint_Satisfaction_Problem):
    def __init__(self):
        # One Constraint Version
        # Initialize a CSP for the one constraint version of the problem
        self.csp_one_constraint = Constraint_Satisfaction_Problem()
        self.csp_one_constraint.name = "send_more_money_one"
        
        # Create domains for each letter
        # Each domain represents possible values (0-9) for each letter in the puzzle
        self.csp_one_constraint.add_domain("s", list(range(0,10)))
        self.csp_one_constraint.add_domain("e", list(range(0,10)))
        self.csp_one_constraint.add_domain("n", list(range(0,10)))
        self.csp_one_constraint.add_domain("d", list(range(0,10)))
        self.csp_one_constraint.add_domain("m", list(range(0,10)))
        self.csp_one_constraint.add_domain("o", list(range(0,10)))
        self.csp_one_constraint.add_domain("r", list(range(0,10)))
        self.csp_one_constraint.add_domain("y", list(range(0,10)))

        
        # Create constraints for the one constraint version
        constraints = []

        # Ensure all letters represent different numbers
        for i in range(len(list(self.csp_one_constraint.domains.keys()))):
            for j in range(i+1, len(list(self.csp_one_constraint.domains.keys()))):
                constraints.append((f"{list(self.csp_one_constraint.domains.keys())[i]} != {list(self.csp_one_constraint.domains.keys())[j]}", [list(self.csp_one_constraint.domains.keys())[i], list(self.csp_one_constraint.domains.keys())[j]]))
        
        # Additional constraints specific to the puzzle
        constraints.append(("s != 0", ["s"]))  # 'S' cannot be 0
        constraints.append(("m != 0", ["m"]))  # 'M' cannot be 0

        # The main arithmetic constraint of the puzzle
        constraints.append(("1000 * s + 100 * e + 10 * n + d + 1000 * m + 100 * o + 10 * r + e == 10000 * m + 1000 * o + 100 * n + 10 * e + y", ["s","e","n","d","m", "o", "r", "y"]))

        # Add all constraints to the CSP
        constraint_counter = 0
        for constraint in constraints:
            constraint_counter += 1
            self.csp_one_constraint.add_constraint(constraint_counter,constraint[0], constraint[1])
        
        # Five Constraint Version
        # Initialize a CSP for the five constraint version of the problem
        self.csp_five_constraint = Constraint_Satisfaction_Problem()
        self.csp_five_constraint.name = "send_more_money_five"
        
        # Create domains for each letter and carry-over digits (c1, c2, c3, c4)
        # Similar to the one constraint version, but with additional domains for carry-over digits in the arithmetic
        self.csp_five_constraint.add_domain("s", list(range(0,10)))
        self.csp_five_constraint.add_domain("e", list(range(0,10)))
        self.csp_five_constraint.add_domain("n", list(range(0,10)))
        self.csp_five_constraint.add_domain("d", list(range(0,10)))
        self.csp_five_constraint.add_domain("m", list(range(0,10)))
        self.csp_five_constraint.add_domain("o", list(range(0,10)))
        self.csp_five_constraint.add_domain("r", list(range(0,10)))
        self.csp_five_constraint.add_domain("y", list(range(0,10)))
        self.csp_five_constraint.add_domain("c1", list(range(0,10)))  # Carry-over digit 1
        self.csp_five_constraint.add_domain("c2", list(range(0,10)))  # Carry-over digit 2
        self.csp_five_constraint.add_domain("c3", list(range(0,10)))  # Carry-over digit 3
        self.csp_five_constraint.add_domain("c4", list(range(0,10)))  # Carry-over digit 4
        
        # Create constraints for the five constraint version
        constraints = []

        # Ensure all letters represent different numbers
        # Similar to the one constraint version
        for i in range(len(list(self.csp_one_constraint.domains.keys()))):
            for j in range(i+1, len(list(self.csp_one_constraint.domains.keys()))):
                constraints.append((f"{list(self.csp_one_constraint.domains.keys())[i]} != {list(self.csp_one_constraint.domains.keys())[j]}", [list(self.csp_one_constraint.domains.keys())[i], list(self.csp_one_constraint.domains.keys())[j]]))
        
        # Additional constraints specific to the puzzle
        constraints.append(("s != 0", ["s"]))  # 'S' cannot be 0
        constraints.append(("m != 0", ["m"]))  # 'M' cannot be 0

        # Arithmetic constraints broken down into smaller parts with carry-over digits
        constraints.append(("d + e == 10 * c1 + y", ["d","e","c1","y"]))
        constraints.append(("n + r + c1 == 10 * c2 + e", ["n","r","c1","c2", "e"]))
        constraints.append(("e + o + c2 == 10 * c3 + n", ["e","o","c2","c3", "n"]))
        constraints.append(("s + m + c3 == 10 * c4 + o", ["s","m","c3","c4", "o"]))
        constraints.append(("c4 == m", ["c4","m"]))

        # Add all constraints to the CSP
        constraint_counter = 0
        for constraint in constraints:
            constraint_counter += 1
            self.csp_five_constraint.add_constraint(constraint_counter,constraint[0], constraint[1])
