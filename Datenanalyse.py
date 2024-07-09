import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# Excel-Datei laden
file_path = 'datenbank.xlsx'  # Pfad zu deiner Excel-Datei
sheet_name = 'Ergebnisse'  # Name des Arbeitsblatts

# Daten aus der Excel-Datei laden
data = pd.read_excel(file_path, sheet_name=sheet_name)

# Dictionary zur Konfiguration der Plots
plot_configs = {
    'plot1': {
        'title': 'Lösungszeiten - 24 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [1, 2, 3, 4, 5, 6, 7, 8],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot2': {
        'title': 'Lösungszeiten - 24 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [9, 10, 11, 12, 13, 14, 15, 16],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot3': {
        'title': 'Lösungszeiten - 24 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [17, 18, 19, 20, 21, 22, 23, 24],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot4': {
        'title': 'Lösungszeiten - 24 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [25, 26, 27, 28, 29, 30, 31, 32],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot5': {
        'title': 'Lösungszeiten - 24 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [33, 34, 35, 36, 37, 38],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot6': {
        'title': 'Lösungszeiten - 24 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [39, 40, 41, 42],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot7': {
        'title': 'Lösungszeiten - 12 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [43, 44, 45, 46, 47, 48, 49, 50],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot8': {
        'title': 'Lösungszeiten - 12 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [51, 52, 53, 54, 55, 56, 57, 58],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot9': {
        'title': 'Lösungszeiten - 12 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [59, 60, 61, 62, 63, 64, 65, 66],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot10': {
        'title': 'Lösungszeiten - 12 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [67, 68, 69, 70, 71, 72, 73, 74],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot11': {
        'title': 'Lösungszeiten - 12 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [75, 76, 77, 78, 79, 80],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot12': {
        'title': 'Lösungszeiten - 12 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [81, 82, 83, 84],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot13': {
        'title': 'Lösungszeiten - 4 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [85, 86, 87, 88, 89, 90, 91, 92],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot14': {
        'title': 'Lösungszeiten - 4 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [93, 94, 95, 96, 97, 98, 99, 100],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot15': {
        'title': 'Lösungszeiten - 4 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [101, 102, 103, 104, 105, 106, 107, 108],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot16': {
        'title': 'Lösungszeiten - 4 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [109, 110, 111, 112, 113, 114, 115, 116],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot17': {
        'title': 'Lösungszeiten - 4 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [117, 118, 119, 120, 121, 122],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot18': {
        'title': 'Lösungszeiten - 4 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [123, 124, 125, 126],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot19': {
        'title': 'Lösungszeiten - 2 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [127, 128, 129, 130, 131, 132, 133, 134],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungszeit (ms)'
    },
    'plot20': {
        'title': 'Lösungsnachrichten - 24 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [1, 2, 3, 4, 5, 6, 7, 8],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot21': {
        'title': 'Lösungsnachrichten - 24 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [9, 10, 11, 12, 13, 14, 15, 16],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot22': {
        'title': 'Lösungsnachrichten - 24 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [17, 18, 19, 20, 21, 22, 23, 24],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot23': {
        'title': 'Lösungsnachrichten - 24 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [25, 26, 27, 28, 29, 30, 31, 32],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot24': {
        'title': 'Lösungsnachrichten - 24 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [33, 34, 35, 36, 37, 38],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot25': {
        'title': 'Lösungsnachrichten - 24 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [39, 40, 41, 42],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot26': {
        'title': 'Lösungsnachrichten - 12 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [43, 44, 45, 46, 47, 48, 49, 50],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot27': {
        'title': 'Lösungsnachrichten - 12 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [51, 52, 53, 54, 55, 56, 57, 58],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot28': {
        'title': 'Lösungsnachrichten - 12 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [59, 60, 61, 62, 63, 64, 65, 66],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot29': {
        'title': 'Lösungsnachrichten - 12 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [67, 68, 69, 70, 71, 72, 73, 74],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot30': {
        'title': 'Lösungsnachrichten - 12 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [75, 76, 77, 78, 79, 80],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot31': {
        'title': 'Lösungsnachrichten - 12 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [81, 82, 83, 84],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot32': {
        'title': 'Lösungsnachrichten - 4 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [85, 86, 87, 88, 89, 90, 91, 92],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot33': {
        'title': 'Lösungsnachrichten - 4 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [93, 94, 95, 96, 97, 98, 99, 100],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot34': {
        'title': 'Lösungsnachrichten - 4 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [101, 102, 103, 104, 105, 106, 107, 108],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot35': {
        'title': 'Lösungsnachrichten - 4 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [109, 110, 111, 112, 113, 114, 115, 116],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot36': {
        'title': 'Lösungsnachrichten - 4 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [117, 118, 119, 120, 121, 122],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot37': {
        'title': 'Lösungsnachrichten - 4 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [123, 124, 125, 126],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot38': {
        'title': 'Lösungsnachrichten - 2 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Lösungsnachrichten [n]',
        'testreihe_ids': [127, 128, 129, 130, 131, 132, 133, 134],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Lösungs-Nachrichten'
    },
    'plot39': {
        'title': 'Wertneuzuweisung - 24 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [1, 2, 3, 4, 5, 6, 7, 8],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot40': {
        'title': 'Wertneuzuweisung - 24 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [9, 10, 11, 12, 13, 14, 15, 16],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot41': {
        'title': 'Wertneuzuweisung - 24 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [17, 18, 19, 20, 21, 22, 23, 24],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot42': {
        'title': 'Wertneuzuweisung - 24 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [25, 26, 27, 28, 29, 30, 31, 32],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot43': {
        'title': 'Wertneuzuweisung - 24 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [33, 34, 35, 36, 37, 38],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot44': {
        'title': 'Wertneuzuweisung - 24 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [39, 40, 41, 42],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot45': {
        'title': 'Wertneuzuweisung - 12 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [43, 44, 45, 46, 47, 48, 49, 50],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot46': {
        'title': 'Wertneuzuweisung - 12 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [51, 52, 53, 54, 55, 56, 57, 58],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot47': {
        'title': 'Wertneuzuweisung - 12 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [59, 60, 61, 62, 63, 64, 65, 66],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot48': {
        'title': 'Wertneuzuweisung - 12 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [67, 68, 69, 70, 71, 72, 73, 74],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot49': {
        'title': 'Wertneuzuweisung - 12 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [75, 76, 77, 78, 79, 80],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot50': {
        'title': 'Wertneuzuweisung - 12 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [81, 82, 83, 84],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot51': {
        'title': 'Wertneuzuweisung - 4 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [85, 86, 87, 88, 89, 90, 91, 92],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot52': {
        'title': 'Wertneuzuweisung - 4 Core-System - 9x9 Sudoku - Level 1',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [93, 94, 95, 96, 97, 98, 99, 100],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot53': {
        'title': 'Wertneuzuweisung - 4 Core-System - 9x9 Sudoku - Level 2',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [101, 102, 103, 104, 105, 106, 107, 108],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot54': {
        'title': 'Wertneuzuweisung - 4 Core-System - 9x9 Sudoku - Level 3',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [109, 110, 111, 112, 113, 114, 115, 116],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot55': {
        'title': 'Wertneuzuweisung - 4 Core-System - 9x9 Sudoku - Level 4',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [117, 118, 119, 120, 121, 122],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot56': {
        'title': 'Wertneuzuweisung - 4 Core-System - 9x9 Sudoku - Level 5',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [123, 124, 125, 126],
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },
    'plot57': {
        'title': 'Wertneuzuweisung - 2 Core-System - 4x4 Sudoku',
        'xlabel': 'Architektur',
        'ylabel': 'Wertneuzuweisung [n]',
        'testreihe_ids': [127, 128, 129, 130, 131, 132, 133, 134],
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)'],
        'parameter': 'Wertveränderungen'
    },

}


output_folder = 'W:\\data\\03_Studium\\Bachelorarbeit\\Grafiken\\Plots'
os.makedirs(output_folder, exist_ok=True)


def sanitize_filename(title):
    umlaut_map = str.maketrans({
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue',
        'ß': 'ss'
    })
    title = title.translate(umlaut_map)
    title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    return title


def create_and_save_plots(data, plot_configs, output_folder):
    for plot_index, (plot_name, config) in enumerate(plot_configs.items(), start=1):
        plt.figure(figsize=(12, 8))

        for idx, test_id in enumerate(config['testreihe_ids']):
            parameter_data = data[data['Testreihe-ID'] == test_id][config['parameter']]
            plt.boxplot(parameter_data, positions=[idx + 1], widths=0.6)

        plt.xlabel(config['xlabel'])
        plt.ylabel(config['ylabel'])
        plt.title(config['title'])
        plt.xticks(range(1, len(config['testreihe_ids']) + 1),
                   config['testreihe_names'],
                   rotation=45, ha='right')

        ymin, ymax = plt.ylim()
        plt.ylim(0, ymax * 1.1)
        plt.ticklabel_format(style='plain', axis='y')

        sanitized_title = sanitize_filename(config['title'])
        filename = f"plot{plot_index}_{sanitized_title}.png"

        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, filename))
        plt.close()



create_and_save_plots(data, plot_configs, output_folder)
