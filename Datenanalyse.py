import pandas as pd

# Lade die Excel-Datei und wähle die Blätter 'Ergebnisse' und 'Übersicht'
file_path = 'datenbank.xlsx'  # Pfad zu deiner Excel-Datei
sheet_ergebnisse = 'Ergebnisse'  # Name des Arbeitsblatts für Ergebnisse
sheet_uebersicht = 'Übersicht'  # Name des Arbeitsblatts für Übersicht

data_ergebnisse = pd.read_excel(file_path, sheet_name=sheet_ergebnisse)
data_uebersicht = pd.read_excel(file_path, sheet_name=sheet_uebersicht)

# Liste der benötigten Spalten
initialization_columns = ['start_solving']
solution_columns = [
    'domain_propagation', 'possible', 'confirm', 'forward_check', 'good_forward_check',
    'bad_forward_check', 'check', 'backtrack', 'backjump', 'nogood', 'start_solving',
    'must_be', 'good', 'unconfirm', 'not_allowed'
]

# Ersetze leere Zellen durch 0 für die benötigten Spalten in Ergebnisse
for col in initialization_columns + solution_columns:
    if col in data_ergebnisse.columns:
        data_ergebnisse[col] = data_ergebnisse[col].fillna(0)
    else:
        data_ergebnisse[col] = 0

# Berechne die Initialisierungs-Nachrichten
data_ergebnisse['Initialisierungs-Nachrichten'] = data_ergebnisse[initialization_columns].sum(axis=1)

# Berechne die Lösungs-Nachrichten
data_ergebnisse['Lösungs-Nachrichten'] = data_ergebnisse[solution_columns].sum(axis=1) - data_ergebnisse[
    initialization_columns].sum(axis=1)

# Berechne die Gesamtanzahl der Nachrichten
data_ergebnisse['Gesamtanzahl der Nachrichten'] = data_ergebnisse['Initialisierungs-Nachrichten'] + data_ergebnisse[
    'Lösungs-Nachrichten']

# Aktualisiere die Spalten in der Übersicht
for index, row in data_uebersicht.iterrows():
    testreihe_id = row['Testreihe-ID']

    # Filtere die entsprechenden Zeilen in Ergebnisse
    filtered_data = data_ergebnisse[data_ergebnisse['Testreihe-ID'] == testreihe_id]

    # Berechne die Gesamt-Lösungszeit (ms)
    data_uebersicht.at[index, 'Gesamt-Lösungszeit (ms)'] = filtered_data['Lösungszeit (ms)'].sum()

    # Berechne die Gesamtanzahl der Nachrichten
    data_uebersicht.at[index, 'Gesamtanzahl der Nachrichten'] = filtered_data['Gesamtanzahl der Nachrichten'].sum()

    # Berechne die Durchschnittliche Lösungszeit (ms)
    data_uebersicht.at[index, 'Durchschnittliche Lösungszeit (ms)'] = filtered_data['Lösungszeit (ms)'].mean()

    # Berechne die Durchschnittliche Anzahl der Nachrichten
    data_uebersicht.at[index, 'Durchschnittliche Anzahl der Nachrichten'] = filtered_data[
        'Gesamtanzahl der Nachrichten'].mean()

# Speichere die bereinigte Datei
output_file_path = 'datenbank_new.xlsx'
with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
    data_ergebnisse.to_excel(writer, sheet_name=sheet_ergebnisse, index=False)
    data_uebersicht.to_excel(writer, sheet_name=sheet_uebersicht, index=False)

print(f"Die Nachrichten wurden erfolgreich berechnet und die Datei '{output_file_path}' wurde aktualisiert.")
