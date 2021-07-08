from z3 import *
from more_z3 import coerce_eq, coerce_ge, coerce_le, IntMatrix, Exactly
import itertools
from puzzles_common import transpose

BLACK, WHITE = 0, 1

def distribute_in_n_direc(n, total):
    assert n >= 2, 'The total is distributed in at least n directions|bins'
    bins = IntVector('b', n)

    minimums = [0] + [1] * (n - 2) + [0]
    min_c = [ coerce_ge(bins, minimums) ] #as a list just for manipulation
    maximums = [total] * n
    max_c = [ coerce_le(bins, maximums) ] #as a list so as to add easily

    sum_c = [ Sum(bins) == total ]

    s = Solver()
    s.add( min_c + max_c + sum_c )
    while s.check() == sat:
        m = s.model()
        solution = tuple( m[b].as_long() for b in bins )
        # solution already seen
        avoid_seen_c = Not(coerce_eq(bins, solution))
        s.add(avoid_seen_c)
        yield solution

def get_patterns_given_runs(runs, length):
    for white_runs in distribute_in_n_direc(len(runs) + 1, length - sum(runs)):
        res = []
        for wr, br in itertools.zip_longest(white_runs, runs, fillvalue=0):
            res.extend([WHITE] * wr)
            res.extend([BLACK] * br)
        yield tuple(res)

def gen_constraints_vars_runs(vars_, runs):
    possibs = [ coerce_eq(vars_, pat)
            for pat in get_patterns_given_runs(runs, len(vars_)) ]
    return Exactly(*possibs, 1)

def solve_pattern(runs_columnwise, runs_rowwise, height, width):
    X = IntMatrix('c', nb_rows=height, nb_cols=width)

    assert len(runs_rowwise) == len(X) == height
    rowwise_c = [ gen_constraints_vars_runs(row, runs)
            for row, runs in zip(X, runs_rowwise)]

    X_trans = transpose(X)

    assert len(runs_columnwise) == len(X_trans) == width
    colwise_c = [ gen_constraints_vars_runs(row, runs)
            for row, runs in zip(X_trans, runs_columnwise)]

    s = Solver()
    s.add( rowwise_c + colwise_c )
    s.check()
    m = s.model()
    return [ [ m[cell] for cell in row] for row in X ]


if __name__ == "__main__":
    pars = {'height': 10,
            'width': 10,
            'runs_columnwise': [(1,),
                (3, 1),
                (7,),
                (2,),
                (1,),
                (3, 1),
                (3, 5),
                (3, 5),
                (2, 1, 5),
                (7,)],
            'runs_rowwise': [(4,),
                (4,),
                (3,),
                (1, 2),
                (3, 1),
                (2, 4),
                (2, 4),
                (1, 4),
                (3, 4),
                (8,)],
            }
    solve_pattern(**pars)

    pars = {'height': 15,
            'width': 20,
            'runs_columnwise': [(1, 3),
                (2, 1, 3, 4),
                (2, 4, 1, 3),
                (2, 5, 3),
                (5, 3),
                (1, 6, 2),
                (3, 5, 1),
                (2, 3),
                (8,),
                (1, 9),
                (3, 6),
                (1, 6),
                (1, 1),
                (1, 3, 2),
                (3, 1, 4, 2),
                (3, 5, 2),
                (2, 5),
                (1, 4),
                (2, 3),
                (3, 1, 1, 1)],
            'runs_rowwise': [(3, 3, 2, 2),
                (3, 2, 1, 2, 3),
                (1, 3, 3, 1),
                (2, 1, 1),
                (1, 2),
                (5, 1),
                (9, 1, 3, 1),
                (2, 13),
                (10, 3, 1),
                (4, 4, 2),
                (2, 4, 4),
                (2, 4, 4),
                (5, 3, 3),
                (6, 2, 5),
                (2, 4, 5)],
            }

    solve_pattern(**pars)
