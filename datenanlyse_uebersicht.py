import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# Excel-Datei laden
file_path = 'datenbank.xlsx'  # Pfad zu deiner Excel-Datei
sheet_name = 'Übersicht'  # Name des neuen Arbeitsblatts

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


# Mapping der Agentensystem-Namen
agentensystem_titel_map = {
    'constraint': 'Problemorientierte Architektur',
    'decentralized': 'Dezentrale Architektur',
    'hierarchical': 'Hierarchische Architektur',
    'combined': 'Spezialisierte Architektur'
}


def create_and_save_plots(data, systeme, agentensysteme, sizes, output_folder, agentensystem_titel_map):
    for size in sizes:
        # Systeme filtern, falls Größe 9x9 ist und System 2 ausgeschlossen werden soll
        if size == '9x9':
            filtered_systeme = sorted([system for system in systeme if system != '2'], key=int)
        else:
            filtered_systeme = sorted(systeme, key=int)

        for agentensystem in agentensysteme:
            data_filtered = data[(data['Agentsystem'] == agentensystem) & (data['Size'] == size)]

            # Debugging-Ausgaben
            print(f"Agentensystem: {agentensystem}, Größe: {size}")
            print(f"Gefilterte Daten: {data_filtered}")

            # Überprüfen, ob gefilterte Daten vorhanden sind
            if data_filtered.empty:
                print(f"Keine Daten für {agentensystem} mit Größe {size}")
                continue

            # Balkendiagramm erstellen
            means = []
            for system in filtered_systeme:
                system_data = data_filtered[data_filtered['System'] == system]['Gesamt-Initialisierungszeit (ms)']
                mean_value = system_data.mean()
                means.append(mean_value)
                print(f"System: {system}, Mittelwert: {mean_value}")

            # Debugging-Ausgaben für Mittelwerte
            print(f"Systeme: {filtered_systeme}")
            print(f"Mittelwerte: {means}")

            # Überprüfen, ob alle Mittelwerte NaN sind
            if all(pd.isna(means)):
                print(f"Keine gültigen Mittelwerte für {agentensystem} mit Größe {size}")
                continue

            plt.figure(figsize=(12, 8))
            plt.bar(filtered_systeme, means)

            # Achsenbeschriftungen und Titel
            agentensystem_title = agentensystem_titel_map.get(agentensystem, agentensystem)
            title = f'Durchschnittliche Initialisierungszeit für {agentensystem_title} ({size})'
            plt.xlabel('System')
            plt.ylabel('Durchschnittliche Initialisierungszeit (ms)')
            plt.title(title)
            plt.xticks(range(len(filtered_systeme)), filtered_systeme, rotation=45, ha='right')

            # Wissenschaftliche Notation deaktivieren
            plt.ticklabel_format(style='plain', axis='y')

            # Dateiname erstellen
            sanitized_title = sanitize_filename(title)
            filename = f"{sanitized_title}.png"

            # Diagramm speichern
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, filename))
            plt.close()


# Plots erstellen und speichern
create_and_save_plots(data, systeme, agentensysteme, sizes, output_folder, agentensystem_titel_map)
