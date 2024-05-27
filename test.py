import itertools

def find_combinations(equation, variable_values):
    keys = variable_values.keys()
    values = itertools.product(*variable_values.values())
    for combination in values:
        if len(set(combination)) != len(combination):
            continue
        expr_copy = equation
        for key, value in zip(keys, combination):
            expr_copy = expr_copy.replace(key, str(value))
        try:
            result = eval(expr_copy)
            if result:
                return {key: value for key, value in zip(keys, combination)}
        except Exception as e:
            continue
    return {}


variable_values = {
    'a1': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'a2': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'a3': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'a4': [4],
    'a5': [1],
    'a6': [6],
    'a7': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'a8': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'a9': [1, 2, 3, 4, 5, 6, 7, 8, 9],
}

equation = "a1 * a2 * a3 * a4 * a5 * a6 * a7 * a8 * a9 == 362880"
print(find_combinations(equation, variable_values))
