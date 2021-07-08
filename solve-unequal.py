from z3 import *
import itertools
from collections import defaultdict
from more_z3 import IntMatrix
from puzzles_common import transpose, flatten, gen_latin_square_constraints

def solve_unequal(puzzle, *, order, lt_inequalities):
    X = IntMatrix('n', order, order)

    latin_c = gen_latin_square_constraints(X, order)


    vars_ = flatten(X)
    vals = flatten(puzzle)
    instance_c  = [ var == val for var, val in zip(vars_, vals)
            if val > 0 ]

    at_ = lambda l, c : X[l][c]
    lesser_than_c = [ at_(*lhs) < at_(*rhs)
            for lhs, rhs in lt_inequalities ]

    s = Solver()
    s.add(latin_c + instance_c + lesser_than_c)

    s.check()
    m = s.model()

    res = [[ m[s] for s in row] for row in X]
    return res


if __name__ == "__main__":
    pars =  {'lt_inequalities': [((3, 1), (2, 1)),
        ((2, 1), (2, 2)),
        ((3, 3), (2, 3)),
        ((2, 2), (3, 2))],
        'order': 4,
        'puzzle': [[0, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]}
    sol = solve_unequal(**pars)

    pars ={'lt_inequalities': [((0, 0), (0, 1)),
        ((0, 2), (0, 3)),
        ((1, 5), (0, 5)),
        ((0, 7), (0, 8)),
        ((2, 2), (1, 2)),
        ((1, 7), (1, 8)),
        ((2, 1), (2, 0)),
        ((3, 0), (2, 0)),
        ((2, 2), (2, 1)),
        ((2, 4), (2, 3)),
        ((1, 4), (2, 4)),
        ((3, 5), (2, 5)),
        ((2, 7), (2, 6)),
        ((4, 1), (3, 1)),
        ((3, 3), (3, 2)),
        ((3, 4), (3, 3)),
        ((4, 6), (3, 6)),
        ((3, 7), (3, 8)),
        ((5, 1), (5, 0)),
        ((4, 0), (5, 0)),
        ((6, 1), (5, 1)),
        ((6, 2), (5, 2)),
        ((4, 4), (5, 4)),
        ((5, 4), (5, 5)),
        ((5, 5), (5, 6)),
        ((5, 6), (5, 7)),
        ((6, 7), (5, 7)),
        ((4, 7), (5, 7)),
        ((6, 0), (6, 1)),
        ((6, 1), (6, 2)),
        ((5, 3), (6, 3)),
        ((5, 5), (6, 5)),
        ((5, 8), (6, 8)),
        ((8, 1), (7, 1)),
        ((7, 4), (7, 3)),
        ((7, 6), (7, 5)),
        ((7, 7), (7, 6)),
        ((8, 8), (7, 8)),
        ((8, 0), (8, 1)),
        ((8, 3), (8, 2)),
        ((8, 4), (8, 3)),
        ((7, 5), (8, 5))],
        'order': 9,
        'puzzle': [[0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 3, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 8, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 4, 0, 0],
            [0, 0, 5, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 5]]}
    sol = solve_unequal(**pars)
