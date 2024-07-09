import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# Excel-Datei laden
file_path = 'datenbank.xlsx'  # Pfad zu deiner Excel-Datei
sheet_name = 'Ergebnisse'  # Name des neuen Arbeitsblatts

# Daten aus der Excel-Datei laden
data = pd.read_excel(file_path, sheet_name=sheet_name)

# Systeme und Agentensysteme aus den Daten extrahieren
data['System'] = data['System'].astype(str)  # Systeme als Strings behandeln
systeme = sorted(data['System'].unique(), key=int)  # Systeme sortieren
agentensysteme = data['Agentsystem'].unique()
sizes = data['Size'].unique()  # Größen extrahieren

# Ordner für die gespeicherten Plots
output_folder = 'W:\\data\\03_Studium\\Bachelorarbeit\\Grafiken\\Plots'
os.makedirs(output_folder, exist_ok=True)


def sanitize_filename(title):
    # Ersetze Umlaute
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
    # Ersetze ungültige Zeichen im Dateinamen durch Unterstriche
    title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    return title


system_comparison_configs = {
    'comparison_plot_9x9_level_1_constraint': {
        'title': 'Problemorientierte Architektur - 9x9 Sudoku - Level 1',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [9, 51, 93],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'constraint'
    },
    'comparison_plot_9x9_level_2_constraint': {
        'title': 'Problemorientierte Architektur - 9x9 Sudoku - Level 2',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [17, 59, 101],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'constraint'
    },
    'comparison_plot_9x9_level_3_constraint': {
        'title': 'Problemorientierte Architektur - 9x9 Sudoku - Level 3',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [25, 67, 109],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'constraint'
    },
    'comparison_plot_9x9_level_4_constraint': {
        'title': 'Problemorientierte Architektur - 9x9 Sudoku - Level 4',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [33, 75, 117],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'constraint'
    },
    'comparison_plot_9x9_level_5_constraint': {
        'title': 'Problemorientierte Architektur - 9x9 Sudoku - Level 5',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [39, 81, 123],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'constraint'
    },
    'comparison_plot_4x4_constraint': {
        'title': 'Problemorientierte Architektur - 4x4 Sudoku',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [1, 43, 85],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'constraint'
    },
    'comparison_plot_9x9_level_1_combined': {
        'title': 'Spezialisierte Architektur - 9x9 Sudoku - Level 1',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [14, 56, 98],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'combined'
    },
    'comparison_plot_9x9_level_2_combined': {
        'title': 'Spezialisierte Architektur - 9x9 Sudoku - Level 2',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [22, 64, 106],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'combined'
    },
    'comparison_plot_9x9_level_3_combined': {
        'title': 'Spezialisierte Architektur - 9x9 Sudoku - Level 3',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [30, 72, 114],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'combined'
    },
    'comparison_plot_9x9_level_4_combined': {
        'title': 'Spezialisierte Architektur - 9x9 Sudoku - Level 4',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [36, 78, 120],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'combined'
    },
    'comparison_plot_9x9_level_5_combined': {
        'title': 'Spezialisierte Architektur - 9x9 Sudoku - Level 5',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [42, 84, 126],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'combined'
    },
    'comparison_plot_4x4_combined': {
        'title': 'Spezialisierte Architektur - 4x4 Sudoku',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [6, 48, 90],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'combined'
    },
    'comparison_plot_9x9_level_1_hierarchical': {
        'title': 'Hierarchische Architektur - 9x9 Sudoku - Level 1',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [12, 54, 96],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'hierarchical'
    },
    'comparison_plot_9x9_level_2_hierarchical': {
        'title': 'Hierarchische Architektur - 9x9 Sudoku - Level 2',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [20, 62, 104],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'hierarchical'
    },
    'comparison_plot_9x9_level_3_hierarchical': {
        'title': 'Hierarchische Architektur - 9x9 Sudoku - Level 3',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [28, 70, 112],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'hierarchical'
    },
    'comparison_plot_4x4_hierarchical': {
        'title': 'Hierarchische Architektur - 4x4 Sudoku',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [4, 46, 88],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'hierarchical'
    },
    'comparison_plot_9x9_level_1_decentralized': {
        'title': 'Dezentrale Architektur - 9x9 Sudoku - Level 1',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [13, 55, 97],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'decentralized'
    },
    'comparison_plot_9x9_level_2_decentralized': {
        'title': 'Dezentrale Architektur - 9x9 Sudoku - Level 2',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [21, 63, 105],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'decentralized'
    },
    'comparison_plot_9x9_level_3_decentralized': {
        'title': 'Dezentrale Architektur - 9x9 Sudoku - Level 3',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [29, 71, 113],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'decentralized'
    },
    'comparison_plot_4x4_decentralized': {
        'title': 'Dezentrale Architektur - 4x4 Sudoku',
        'xlabel': 'System',
        'ylabel': 'Lösungszeit [ms]',
        'testreihe_ids': [5, 47, 89],
        'testreihe_names': ['24 Core', '12 Core', '4 Core'],
        'parameter': 'Lösungszeit (ms)',
        'architecture': 'decentralized'
    }
}


def create_and_save_comparison_plots(configs, data):
    for config_name, config in configs.items():
        plt.figure(figsize=(12, 8))

        # Daten filtern nach Architektur und Testreihe-IDs
        data_filtered = data[
            (data['Agentsystem'] == config['architecture']) & (data['Testreihe-ID'].isin(config['testreihe_ids']))]

        # Debugging-Ausgaben
        print(f"Gefilterte Daten für {config_name}: {data_filtered}")

        # Boxplot erstellen
        data_to_plot = [data_filtered[data_filtered['Testreihe-ID'] == testreihe_id][config['parameter']].dropna() for
                        testreihe_id in config['testreihe_ids']]

        # Debugging-Ausgaben für die Daten, die geplottet werden
        print(f"Daten zum Plotten für {config_name}: {data_to_plot}")

        plt.boxplot(data_to_plot, tick_labels=config['testreihe_names'])

        # Achsenbeschriftungen und Titel
        plt.xlabel(config['xlabel'])
        plt.ylabel(config['ylabel'])
        plt.title(config['title'])
        plt.xticks(rotation=45, ha='right')

        # Wissenschaftliche Notation deaktivieren
        plt.ticklabel_format(style='plain', axis='y')

        # Dateiname erstellen
        sanitized_title = sanitize_filename(config['title'])
        filename = f"{sanitized_title}.png"

        # Diagramm speichern
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, filename))
        plt.close()


# Erstellen und speichern der Vergleichsplots
create_and_save_comparison_plots(system_comparison_configs, data)
