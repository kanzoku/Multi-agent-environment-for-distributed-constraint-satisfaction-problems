import pandas as pd
import random

def generate_full_sudoku():
    base = 3
    side = base * base
    def pattern(r, c):
        return (base * (r % base) + r // base + c) % side
    def shuffle(s):
        return random.sample(s, len(s))
    rBase = range(base)
    rows = [g * base + r for g in shuffle(rBase) for r in shuffle(rBase)]
    cols = [g * base + c for g in shuffle(rBase) for c in shuffle(rBase)]
    nums = shuffle(range(1, base * base + 1))
    board = [[nums[pattern(r, c)] for c in cols] for r in rows]
    return board

def create_sudoku_puzzle(board, empties=60):
    puzzle = [row[:] for row in board]
    squares = len(board) * len(board)
    for p in random.sample(range(squares), empties):
        puzzle[p // len(board)][p % len(board)] = 0
    return puzzle

def is_valid(board, row, col, num):
    for x in range(9):
        if board[row][x] == num or board[x][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def solve_sudoku(board):
    def find_empty_location(board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None

    empty_spot = find_empty_location(board)
    if not empty_spot:
        return True
    row, col = empty_spot
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            if solve_sudoku(board):
                return True
            board[row][col] = 0
    return False

def generate_and_save_sudokus(file_name='sudoku_datenbank.xlsx', sheet_name='9x9', num_sudokus=500):
    sudoku_list = []
    for _ in range(num_sudokus):
        full_board = generate_full_sudoku()
        puzzle_board = create_sudoku_puzzle(full_board, empties=55)
        while not solve_sudoku([row[:] for row in puzzle_board]):
            full_board = generate_full_sudoku()
            puzzle_board = create_sudoku_puzzle(full_board, empties=55)
        print(f"Generiere Sudoku {len(sudoku_list) + 1} von {num_sudokus}.")
        flat_board = [num for row in puzzle_board for num in row]
        sudoku_list.append(flat_board)

    columns = [f'{chr(97 + (i // 26)) + chr(97 + (i % 26)) if i >= 26 else chr(97 + i)}' for i in range(81)]

    df = pd.DataFrame(sudoku_list, columns=columns)
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, startrow=1, sheet_name=sheet_name)

    print(f"Die Sudokus wurden erfolgreich in '{file_name}' im Worksheet '{sheet_name}' gespeichert.")


def read_sudoku_to_dict(file_name, sheet_name, row_number):
    # Lade die Excel-Datei und das spezifische Worksheet
    df = pd.read_excel(file_name, sheet_name=sheet_name)

    # Zugriff auf die spezifische Zeile (Index ist row_number - 1)
    sudoku_row = df.iloc[row_number - 1].tolist()

    # Spaltennamen für das Sudoku-Board
    column_labels = [f"{chr(97 + i)}{j + 1}" for i in range(9) for j in range(9)]

    # Initialisiere das Dictionary
    occupation_dict = {label: None for label in column_labels}

    # Fülle das Dictionary mit den Werten aus der Excel-Zeile
    for label, value in zip(column_labels, sudoku_row):
        if value == 0:
            occupation_dict[label] = None
        else:
            occupation_dict[label] = value

    return occupation_dict

def read_sudoku(number = 2):
    row_number = number +1
    file_name = 'sudoku_datenbank.xlsx'
    sheet_name = '9x9'
    occupation_dict = read_sudoku_to_dict(file_name, sheet_name, row_number)
    # print(occupation_dict)
    return occupation_dict


if __name__ == "__main__":
    generate_and_save_sudokus()
