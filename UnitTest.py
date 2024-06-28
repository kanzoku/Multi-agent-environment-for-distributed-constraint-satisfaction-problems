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


def generate_and_save_sudokus(file_name='sudoku_datenbank.xlsx', sheet_name='9x9', num_sudokus=20):
    sudoku_list = []
    for _ in range(num_sudokus):
        full_board = generate_full_sudoku()
        puzzle_board = create_sudoku_puzzle(full_board, empties=61)
        while not solve_sudoku([row[:] for row in puzzle_board]):
            full_board = generate_full_sudoku()
            puzzle_board = create_sudoku_puzzle(full_board, empties=61)
        print(f"Generiere Sudoku {len(sudoku_list) + 1} von {num_sudokus}.")
        flat_board = [num for row in puzzle_board for num in row]
        sudoku_list.append(flat_board)

    columns = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9',
               'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9',
               'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9',
               'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9',
               'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9',
               'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
               'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8', 'g9',
               'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9',
               'i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9']

    df = pd.DataFrame(sudoku_list, columns=columns)
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, startrow=0, sheet_name=sheet_name)

    print(f"Die Sudokus wurden erfolgreich in '{file_name}' im Worksheet '{sheet_name}' gespeichert.")


def read_sudoku_to_dict(file_name, sheet_name, row_number):
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    sudoku_row = df.iloc[row_number - 1].tolist()
    if sheet_name == "4x4":
        column_labels = [f"{chr(97 + i)}{j + 1}" for i in range(4) for j in range(4)]
    else:
        column_labels = [f"{chr(97 + i)}{j + 1}" for i in range(9) for j in range(9)]
    occupation_dict = {label: None for label in column_labels}
    for label, value in zip(column_labels, sudoku_row):
        if value == 0:
            occupation_dict[label] = None
        else:
            occupation_dict[label] = value
    return occupation_dict


def read_sudoku(number, size, level, test_number=0):
    if test_number == 4:
        occupation_dict = {"a1": None, "a2": None, "a3": None, "a4:": None,
                           "b1": None, "b2": None, "b3": None, "b4": None,
                           "c1": None, "c2": None, "c3": None, "c4": None,
                           "d1": None, "d2": None, "d3": None, "d4": None}
        print(occupation_dict)
        return occupation_dict
    row_number = number + ((level - 1) * 100)
    file_name = 'sudoku_datenbank.xlsx'
    sheet_name = size
    print(f"Requested sheet name: {sheet_name}")  # Debugging-Ausgabe
    sheet_names = pd.ExcelFile(file_name).sheet_names
    print(f"Available sheets: {sheet_names}")  # Debugging-Ausgabe
    if sheet_name not in sheet_names:
        raise ValueError(f"Sheet '{sheet_name}' does not exist in the file.")
    occupation_dict = read_sudoku_to_dict(file_name, sheet_name, row_number)
    print(f"Das Sudoku mit der Nummer {number} in Zeile {number + 1} wurde erfolgreich eingelesen.")
    print(occupation_dict)
    return occupation_dict


if __name__ == "__main__":
    generate_and_save_sudokus()
