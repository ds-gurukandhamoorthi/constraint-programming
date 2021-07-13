from z3 import *
from more_z3 import IntMatrix, Exactly, coerce_eq
from puzzles_common import flatten, transpose
from more_itertools import pairwise
import itertools
from collections import defaultdict

HORIZ_START, HORIZ_END, VERTIC_START, VERTIC_END = -1, -2, 1, 2

def normalize_domino(domino):
    return tuple(sorted(domino))

def solve_puzzle_dominosa(puzzle, *, height, width, order):
    board = IntMatrix('d', nb_rows=height, nb_cols=width)

    complete_c = [ Exactly( cell == VERTIC_START, cell == VERTIC_END,
            cell == HORIZ_START, cell == HORIZ_END, 1)
            for cell in flatten(board) ]

    _no_aberrant_horiz_c = []
    for row in board:
        for domino in pairwise(row):
            # not-head and tail
            abberrant_1 = And(domino[0] != HORIZ_START, domino[1] == HORIZ_END)
            # head and not-tail
            _no_aberrant_horiz_c.append(Not(abberrant_1))
            abberrant_2 = And(domino[0] == HORIZ_START, domino[1] != HORIZ_END)
            _no_aberrant_horiz_c.append(Not(abberrant_2))

    _no_aberrant_vertic_c = []
    for row in transpose(board):
        for domino in pairwise(row):
            # not-head and tail
            abberrant_1 = And(domino[0] != VERTIC_START, domino[1] == VERTIC_END)
            _no_aberrant_vertic_c.append(Not(abberrant_1))
            # head and not-tail
            abberrant_2 = And(domino[0] == VERTIC_START, domino[1] != VERTIC_END)
            _no_aberrant_vertic_c.append(Not(abberrant_2))

    _no_aberrant_horiz_border_cell_c = [And(row[0] != HORIZ_END, row[-1] != HORIZ_START)
            for row in board]

    _no_aberrant_vertic_border_cell_c = [And(row[0] != VERTIC_END, row[-1] != VERTIC_START)
            for row in transpose(board)]

    no_aberrant_c = ( _no_aberrant_horiz_c + _no_aberrant_horiz_border_cell_c +
                    _no_aberrant_vertic_c + _no_aberrant_vertic_border_cell_c )

    # By taking both the start_variable and end_variable we may not
    # need no_aberrant_c ... but it's better separated this way.
    unique_c = []
    locs_h = defaultdict(list) #locations
    for var_row, row in zip(board, puzzle):
        for var, dom in zip(var_row, pairwise(row)):
            locs_h[normalize_domino(dom)].append(var)
    locs_v = defaultdict(list)
    for var_row, row in zip(transpose(board), transpose(puzzle)):
        for var, dom in zip(var_row, pairwise(row)):
            locs_v[normalize_domino(dom)].append(var)
    # normalized domino
    for n_domino in itertools.combinations_with_replacement(range(order + 1), 2):
        if n_domino in locs_h and n_domino in locs_v:
            only_one_such_domino = Exactly(*[edge == VERTIC_START for edge in locs_v[n_domino]],
                *[edge == HORIZ_START for edge in locs_h[n_domino]],
                1)
            unique_c.append(only_one_such_domino)
        elif n_domino not in locs_h:
            only_one_such_domino = Exactly(*[edge == VERTIC_START for edge in locs_v[n_domino]], 1)
            unique_c.append(only_one_such_domino)
        elif n_domino not in locs_v:
            only_one_such_domino = Exactly(*[edge == HORIZ_START for edge in locs_h[n_domino]], 1)
            unique_c.append(only_one_such_domino)

    s = Solver()
    s.add(complete_c + no_aberrant_c + unique_c)
    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board]

if __name__ == "__main__":
    pars = {'height': 4,
            'order': 3,
            'puzzle': [[1, 3, 0, 2, 1], [3, 1, 2, 3, 1], [2, 2, 1, 3, 2], [0, 0, 0, 3, 0]],
            'width': 5}

    solve_puzzle_dominosa(**pars)

    pars = {'height': 11,
            'order': 10,
            'puzzle': [[6, 1, 2, 1, 4, 5, 4, 6, 0, 4, 4, 7],
                [5, 10, 2, 4, 10, 1, 7, 3, 2, 2, 4, 0],
                [3, 1, 0, 4, 8, 4, 7, 9, 5, 0, 6, 10],
                [9, 2, 6, 10, 1, 10, 8, 6, 8, 7, 1, 1],
                [5, 3, 3, 7, 1, 7, 0, 0, 0, 4, 3, 3],
                [6, 2, 10, 3, 6, 2, 3, 4, 9, 10, 7, 5],
                [9, 1, 0, 9, 9, 9, 0, 5, 9, 3, 6, 9],
                [3, 9, 10, 7, 9, 6, 6, 2, 5, 8, 2, 8],
                [8, 7, 7, 10, 2, 0, 1, 3, 1, 5, 8, 4],
                [8, 10, 0, 10, 2, 8, 4, 1, 8, 2, 8, 0],
                [8, 5, 7, 5, 5, 5, 3, 7, 10, 6, 6, 9]],
            'width': 12}
    solve_puzzle_dominosa(**pars)
