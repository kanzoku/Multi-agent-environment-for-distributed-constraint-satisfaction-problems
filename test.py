import itertools
import time
import random

def lineare_suche(permutationen, ziele):
    ergebnisse = []
    for ziel in ziele:
        for perm in permutationen:
            if perm == ziel:
                ergebnisse.append(perm)
                break
    return ergebnisse

def set_suche(permutationen, ziele):
    perm_set = set(permutationen)
    ergebnisse = [ziel for ziel in ziele if ziel in perm_set]
    return ergebnisse

def hash_suche(permutationen, ziele):
    perm_dict = {perm: index for index, perm in enumerate(permutationen)}
    ergebnisse = [ziel for ziel in ziele if ziel in perm_dict]
    return ergebnisse

zahlen = range(1, 10)
permutationen = list(itertools.permutations(zahlen))


# random.seed(0)
# ziel_kombinationen = random.sample(permutationen, 100)

ziel_kombinationen = [
    (1, 2, 3, 4, 5, 6, 7, 8, 9),
    (2, 3, 4, 5, 6, 7, 8, 9, 1),
    (3, 4, 5, 6, 7, 8, 9, 1, 2),
    (4, 5, 6, 7, 8, 9, 1, 2, 3),
    (5, 6, 7, 8, 9, 1, 2, 3, 4),
    (6, 7, 8, 9, 1, 2, 3, 4, 5),
    (7, 8, 9, 1, 2, 3, 4, 5, 6),
    (8, 9, 1, 2, 3, 4, 5, 6, 7),
    (9, 1, 2, 3, 4, 5, 6, 7, 8),
    (1, 3, 5, 7, 9, 2, 4, 6, 8),
]

start_time = time.time()
resultat = lineare_suche(permutationen, ziel_kombinationen)
end_time = time.time()
print("Lineare Suche Zeit:", (end_time - start_time) * 1000, "ms, Ergebnis:", resultat)

# Set-basierte Suche
start_time = time.time()
resultat = set_suche(permutationen, ziel_kombinationen)
end_time = time.time()
print("Set Suche Zeit:", (end_time - start_time) * 1000, "ms, Ergebnis:", resultat)

# Hash-basierte Suche
start_time = time.time()
resultat = hash_suche(permutationen, ziel_kombinationen)
end_time = time.time()
print("Hash Suche Zeit:", (end_time - start_time) * 1000, "ms, Ergebnis:", resultat)
