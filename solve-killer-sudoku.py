from z3 import *
import itertools
from more_z3 import IntMatrix
from puzzles_common import transpose, gen_latin_square_constraints, get_same_block_indices

ORDER = 9

def get_nonet_id(row, col):
    return row//3 * 3 + col // 3

NONETS_IDS = [ [ get_nonet_id(l, c) for c in range(ORDER) ]
        for l in range(ORDER) ]

def solve_killer_sudoku(puzzle, *, sums):
    X = IntMatrix('n', ORDER, ORDER)

    at_ = lambda l, c : X[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    latin_c = gen_latin_square_constraints(X, ORDER)

    nonet_c = []
    nonets_inds = get_same_block_indices(NONETS_IDS)
    for board_indices in nonets_inds.values():
        vars_ = get_vars_at(board_indices)
        nonet_c.append(Distinct(vars_))

    #sum of distinct numbers
    cage_c = []
    cages_inds = get_same_block_indices(puzzle)
    for sums_ind, cage_indices in cages_inds.items():
        vars_ = get_vars_at(cage_indices)
        cstrnt = And(Distinct(vars_), Sum(vars_) == sums[sums_ind])
        cage_c.append(cstrnt)

    s = Solver()
    s.add( latin_c + nonet_c + cage_c )
    s.check()
    
    m = s.model()
    return [ [m[cell] for cell in row] for row in X]


if __name__ == "__main__":
    pars = {
            'puzzle': ((0,0,1,1,1,2,3,4,5),
                (6,6,7,7,2,2,3,4,5),
                (6,6,8,8,2,9,10,10,5),
                (11,12,12,8,13,9,10,14,5),
                (11,15,15,16,13,9,14,14,17),
                (18,15,19,16,13,20,21,21,17),
                (18,19,19,16,22,20,20,23,23),
                (18,24,25,22,22,26,26,23,23),
                (18,24,25,22,27,27,27,28,28)),

            'sums': [3,15,22,4,16,15,25,17,9,8,20,6,14,17,17,13,20,12,27,6,20,6,10,14,8,16,15,13,17]
            }

    solve_killer_sudoku(**pars)
