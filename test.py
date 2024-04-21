# Lösung als Dictionary
solution = {'a1': 1, 'a2': 7, 'a3': 3, 'a4': 9, 'a5': 6, 'a6': 4, 'a7': 8, 'a8': 5, 'a9': 2,
            'b1': 5, 'b2': 6, 'b3': 4, 'b4': 1, 'b5': 8, 'b6': 2, 'b7': 3, 'b8': 9, 'b9': 7,
            'c1': 8, 'c2': 2, 'c3': 9, 'c4': 3, 'c5': 5, 'c6': 7, 'c7': 1, 'c8': 6, 'c9': 4,
            'd1': 3, 'd2': 1, 'd3': 2, 'd4': 8, 'd5': 4, 'd6': 6, 'd7': 9, 'd8': 7, 'd9': 5,
            'e1': 9, 'e2': 8, 'e3': 7, 'e4': 2, 'e5': 1, 'e6': 5, 'e7': 4, 'e8': 3, 'e9': 6,
            'f1': 6, 'f2': 4, 'f3': 5, 'f4': 7, 'f5': 9, 'f6': 3, 'f7': 2, 'f8': 1, 'f9': 8,
            'g1': 2, 'g2': 3, 'g3': 8, 'g4': 6, 'g5': 7, 'g6': 9, 'g7': 5, 'g8': 4, 'g9': 1,
            'h1': 7, 'h2': 5, 'h3': 1, 'h4': 4, 'h5': 3, 'h6': 8, 'h7': 6, 'h8': 2, 'h9': 9,
            'i1': 4, 'i2': 9, 'i3': 6, 'i4': 5, 'i5': 2, 'i6': 1, 'i7': 7, 'i8': 8, 'i9': 3}

# Erstellen der Sudoku-Matrix
sudoku = []
for row in range(1, 10):  # Für jede Zeile 1 bis 9
    row_values = []
    for col in "abcdefghi":  # Für jede Spalte a bis i
        key = col + str(row)
        row_values.append(solution[key])
    sudoku.append(row_values)

# Drucke das Sudoku schön formatiert
for line in sudoku:
    print(" ".join(map(str, line)))

# occupation_dict = {}  # Initialisiert das Wörterbuch
#
# for col in "abcdefghi":  # Geht durch die Buchstaben a bis i
#     for row in range(1, 10):  # Geht durch die Zahlen 1 bis 9
#         key = col + str(row)  # Erstellt den Schlüssel wie 'a1', 'a2', usw.
#         occupation_dict[key] = None  # Weist jedem Schlüssel den Wert None zu
#
# # Um alle Zuweisungen zu überprüfen, könnten wir sie ausdrucken
# for key, value in occupation_dict.items():
#     print(f'occupation_dict["{key}"] = {value}')