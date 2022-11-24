import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, gen_latin_square_constraints, get_same_block_indices
from more_itertools import windowed

def sorted_equal(vars_, vals):
    assert len(vars_) == len(vals), "variables and values must have same length"
    perms = itertools.permutations(vals)
    return Or([ coerce_eq(vars_, perm) for perm in perms ])


def solve_puzzle_renban(*, order, cage_ids, instance):
    board = IntMatrix('n', nb_rows=order, nb_cols=order)

    latin_c = gen_latin_square_constraints(board, order)

    at_ = lambda l, c : board[l][c]
    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(order), range(order))
            if instance[l][c] > 0 ]

    consecutive_cage_c = []

    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]
    cages_inds = get_same_block_indices(cage_ids)
    for board_indices in cages_inds.values():
        cage_size = len(board_indices)
        if cage_size > 1:
            vars_ = get_vars_at(board_indices)
            possibs = []
            for wnd in windowed(range(1, order + 1), cage_size):
                possibs.append(sorted_equal(vars_, wnd))
            cnstrnt = Or(possibs)
            consecutive_cage_c.append(cnstrnt)

    s = Solver()

    s.add( latin_c + instance_c + consecutive_cage_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Renban/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'order': 7,
            'cage_ids':
            ( (0,1,2,2,3,4,4),
                (0,0,5,6,3,4,4),
                (7,8,8,6,3,9,9),
                (7,10,11,6,12,13,9),
                (14,10,10,12,12,15,15),
                (16,17,18,18,18,15,15),
                (16,16,16,16,19,20,15)),
            'instance':
            (   (3,0,0,1,4,0,7),
                (0,0,7,0,0,6,0),
                (0,5,0,0,2,0,0),
                (0,0,0,0,5,0,0),
                (0,0,0,0,0,0,0),
                (0,0,3,0,1,0,0),
                (0,0,0,0,0,0,0)),
            }
    solve_puzzle_renban(**pars)
