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

import numpy as np
import networkx as nx
import math
import pandas as pd
import tkinter as tk
from tkinter import filedialog


class Constraint:
    """
    Represents a constraint in a constraint satisfaction problem (CSP).

    Attributes:
        constraint_id (int): Unique identifier of the constraint.
        variables (list): List of variables involved in the constraint.
        func (function): The constraint equation defined as a function.
        degree (int): Degree of the constraint.
        type (str): Type of the constraint, either 'hard' or 'soft'.
        constraint_string (str): String representation of the constraint equation.
        active (bool): Status of the constraint (active or not).
        costs (float): Associated costs with the constraint.
    """

    def __init__(self, constraint_id, variables, func, degree, constraint_type, constraint_string, costs):
        """
        Initializes a new instance of the Constraint class.

        Args:
            nr (int): Unique identifier of the constraint.
            variables (list): List of variables involved in the constraint.
            func (function): The constraint equation defined as a function.
            degree (int): Degree of the constraint.
            constraint_type (str): Type of the constraint, either 'hard' or 'soft'.
            constraint_string (str): String representation of the constraint equation.
            costs (float): Associated costs with the constraint.
        """
        self.constraint_id = constraint_id
        self.variables = variables
        self.func = func
        self.degree = degree
        self.type = constraint_type
        self.constraint_string = constraint_string
        self.active = True
        self.costs = costs

    def is_satisfied(self, values):
        """
        Checks if the constraint is satisfied given a set of variable values.

        Args:
            values (dict): A dictionary of variable values, where keys are variable names
                           and values are the assigned values to these variables.

        Returns:
            bool: True if the constraint is satisfied, False otherwise.
        """
        return self.func(**values)


class Constraint_Satisfaction_Problem:
    """
    Represents a constraint satisfaction problem.

    Attributes:
        domains (dict): Domains of the CSP, where keys are variable names and values are lists of possible values.
        constraints (list): A list of Constraint objects representing the constraints of the CSP.
        input_variables(list): A list of all input variables
    """

    def __init__(self):
        self.domains = {}
        self.constraints = []
        self.input_variables = []

    def add_domain(self, name, domain):
        """
        Add a new Domain at the constraint satisfaction problem.

        Args:
            name (string): The name of the domain.
            domain (dict): Domains of the CSP, where values are lists of possible values.
        """
        self.domains[name] = domain

    def define_input_variables(self, variables):
        """
        Define the input variables at the constraint satisfaction problem.

        Args:
            variables (list): A list of all input variables.
        """
        self.input_variables = variables

    def set_domain(self, name, domain):
        """
        Change a domain at the constraint satisfaction problem.

        Args:
            name (string): The name of the domain.
            domains (dict): Domains of the CSP, where values are lists of possible values.
        """
        self.domains[name] = [domain]

    def add_constraint(self, constraint_id, constraint_string, variables, constraint_type="hard", costs=None):
        """
        Add a constraint at the constraint satisfaction problem.

        Args:
            constraint_id (int): Unique identifier of the constraint.
            constraint_string (str): String representation of the constraint equation.
            variables (list): List of variables involved in the constraint.
            constraint_type (str): Type of the constraint, either 'hard' or 'soft'.
            costs (float): Associated costs with the constraint.
        """

        # Checks whether all constraint variables are also created in the CSP.
        for var1 in variables:
            error = True
            for var2 in self.domains.keys():
                if var1 == var2:
                    error = False

            if error == True:
                print("Error: At least one constraint variable is not yet present in the CSP variables.")
                print(constraint_string)
                return "Error"

        # Creates the constraint equation as a function
        def constraint_func(**kwargs):
            """
            Creates the constraint equation as a function.

            Args:
                **kwargs (dict): Value assignments of the domains whose consistency is to be checked. Example: {"a": 1, "b": 2, "c": 3}

            """

            constraint_string_modify = constraint_string
            # if constraint_string_modify == '(f2_d_join**(2)-f2_d_mat1**(2))*f2_l_join==(f3_d_mat2**(2)-f3_d_1**(2))*f3_l_mat2':
            # print('yes')
            for variable in variables:
                constraint_string_modify = constraint_string_modify.replace(variable, str(
                    kwargs[variable]))  # Erstetzen der Variablen mit ihrne Wertebelegungen
            # Wahrheitswert überprüfen
            return eval(f'{constraint_string_modify}')

        # Calculate the constraint degree
        degree = len(variables)

        if costs == 0 or "":
            costs = None

        # Append the constraint as instance of the Constraint class to the constraints list
        self.constraints.append(
            Constraint(constraint_id, variables, constraint_func, degree, constraint_type, constraint_string, costs))

    def create_graph(self):
        """
        Creates a graph of the constraint satisfaction problem.
        """
        self.graph = nx.Graph()

        # Add the variables as nodes
        for variable in self.domains.keys():
            self.graph.add_node(variable)

        # Add the constraints as edges
        edges = []
        for constraint in self.constraints:
            for var1 in constraint.variables:
                for var2 in constraint.variables:
                    if var1 != var2 and (var1, var2) not in edges and (var2, var1) not in edges:
                        edges.append((var1, var2))

        for edge in edges:
            self.graph.add_edge(*edge)  # unpack edge tuple*

        return self.graph

    def draw_graph(self):
        """
        Draw a image of the graph
        """
        nx.draw(self.graph, with_labels=True, font_weight='bold')

    def summarize_csp(self):
        """
        Summarize the csp
        """

        # Number of variables
        num_variables = len(self.domains)

        # Number of all domain values
        init_num_domain_values = sum(len(self.domains[domain]) for domain in self.domains)

        # Number of possible solutions
        init_num_possible_solutions = 1

        for domain in self.domains:
            init_num_possible_solutions *= len(self.domains[domain])

        init_num_possible_solutions = "%.2e" % (init_num_possible_solutions)

        # Number of unary, binary and n-ary constraints
        unary_constraints = sum(1 for constraint in self.constraints if constraint.degree == 1)
        binary_constraints = sum(1 for constraint in self.constraints if constraint.degree == 2)
        n_ary_constraints = len(self.constraints) - unary_constraints - binary_constraints

        # Degree of cross-linking
        variable_connections = {var: 0 for var in self.domains.keys()}  # Nochmal überprüfen
        for var in variable_connections:
            for constraint in self.constraints:
                if var in constraint.variables:
                    variable_connections[var] += 1
            avg_degree = sum(variable_connections.values()) / num_variables

        print('Number of variables: ', num_variables, '\nSize of the solution space:', init_num_possible_solutions)
        print('Number of constraints: ', len(self.constraints), '\nNumber of unary constraints: ', unary_constraints,
              '\nNumber of binary constraints: ', binary_constraints, '\nNumber of n-ary constraints: ',
              n_ary_constraints)
        print('Variable connecting degree: ', avg_degree)

    def csp_from_excel(self, file=None):
        """
        Initializes the CSP (Constraint Satisfaction Problem) from an Excel file.
        If no file is specified, opens a file dialog for the user to select an Excel file.

        Args:
            file: Optional; the path to the Excel file containing variables and constraints.
        """

        if file is None:
            # Initialize a Tkinter window
            root = tk.Tk()
            # Hide the main Tkinter window
            root.withdraw()
            # Open the file explorer and ask for a file path
            file = filedialog.askopenfilename()

        # Read the domains from Excel
        excel_variables = pd.read_excel(file, "variables")
        self.domains = {}  # Reset the domains dictionary

        for row in range(len(excel_variables)):
            domain_str = str(excel_variables.loc[row, "domain"])
            variable = excel_variables.loc[row, "name"]

            # If there is a dash ('-'), it indicates a continuous domain, e.g., from 1 to 5
            if domain_str.find("-") != -1:
                domain_str = domain_str.replace(" ", "").split(
                    "-")  # Split the domain at the dash and convert to a list
                domain = list(range(int(domain_str[0]), int(domain_str[1]) + 1))

            # If there is a comma (','), it indicates a discrete domain, e.g., 5,10,15,...
            elif domain_str.find(",") != -1:
                domain_str = domain_str.replace(" ", "").split(
                    ",")  # Split the domain at the comma and convert to a list
                domain = list(map(int, domain_str))

            # If 'linspace' is found, evaluate the expression to generate the domain
            elif domain_str.find("linspace") != -1:
                domain = list(eval(domain_str))

            # If the domain is a single value, convert it to a list
            else:
                domain = [int(domain_str)]

            self.domains[variable] = domain

        # Read the constraints from Excel
        excel_constraints = pd.read_excel(file, "constraints")  # Read the constraints sheet
        self.constraints = []  # Reset the constraints list
        constraint_id = 0
        for row in range(len(excel_constraints)):
            # Create the constraints as edges in the CSP
            constraint_id += 1
            self.add_constraint(constraint_id=constraint_id, constraint_string=excel_constraints.loc[row, "constraint"],
                                variables=excel_constraints.loc[row, "variables"].replace(" ", "").split(","),
                                constraint_type=excel_constraints.loc[row, "priority"],
                                costs=excel_constraints.loc[row, "cost"])


# -----------------------------------------------------------------------------
# Example use
# -----------------------------------------------------------------------------

# Create the constraint satisfaction problem as instance
#csp = Constraint_Satisfaction_Problem()
# file = r"C:\Users\Herrmann\Documents\Herrmann\Meine Bibliothek\08_Forschung\csp_solution_envioment\csp_definition.xlsx"
#csp.csp_from_excel()

# Add the variables
# csp.add_domain("x", list(range(1,4)))
# csp.add_domain("y", list(range(1,4)))
# csp.add_domain("z", list(range(1,4)))

# Add the constraints
# csp.add_constraint(1,'x + y == z', ["x","y","z"])
# csp.add_constraint(2,'x < y', ["x","y"])
# csp.add_constraint(3,'z > y', ["y", "z"])
# csp.add_constraint(4,'x == 2', ["x"])

# solver = CSP_Solver(csp.domains, csp.constraints)
# solver.solve(max_solutions=3, constraint_propagation="AC-3", search_algorithm=None)
