import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, transpose
from more_itertools import windowed

EMPTY = 0

def solve_puzzle_hanare(*, height, width, cage_ids, instance):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    # range of variable in each cage
    cage_range_c = []
    # There is exactly one cell containing (bearing) the size of the cage
    cage_size_bearer_c = []
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        cage_size = len(vars_)
        cnstrnt = And([ Xor(var == EMPTY, var == cage_size) for var in vars_ ])
        cage_range_c.append(cnstrnt)
        cnstrnt = Exactly( *[ var == cage_size for var in vars_ ], 1)
        cage_size_bearer_c.append(cnstrnt)

    # the distance at which the neighbour must be.
    distance_c = []
    for i in range( width + 1 - 2 ):
        for row in board:
            for wnd in windowed(row, i+2):
                if i == 0:
                    cell_l, cell_r = wnd
                    condition = And(cell_l > 0, cell_r > 0)
                    necessary_distance = cell_l == cell_r #distance = 0
                    cnstrnt = Implies(condition, necessary_distance)
                else:
                    cell_l, *in_between, cell_r = wnd
                    condition = And(cell_l > 0, cell_r > 0, *[ cell == 0 for cell in in_between ])
                    necessary_distance = Or(cell_l - cell_r == i, cell_r - cell_l == i)
                    cnstrnt = Implies(condition, necessary_distance)
                distance_c.append(cnstrnt)
    for i in range( height + 1 - 2 ):
        for col in transpose(board):
            for wnd in windowed(col, i+2):
                if i == 0:
                    cell_t, cell_b = wnd
                    condition = And(cell_t > 0, cell_b > 0)
                    necessary_distance = cell_t == cell_b #distance = 0
                    cnstrnt = Implies(condition, necessary_distance)
                else:
                    cell_t, *in_between, cell_b = wnd
                    condition = And(cell_t > 0, cell_b > 0, *[ cell == 0 for cell in in_between ])
                    necessary_distance = Or(cell_t - cell_b == i, cell_b - cell_t == i)
                    cnstrnt = Implies(condition, necessary_distance)
                distance_c.append(cnstrnt)

    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(height), range(width))
            if instance[l][c] > 0 ]

    s = Solver()

    s.add( cage_range_c + cage_size_bearer_c + distance_c + instance_c )

    s.check()
    m = s.model()

    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Hanare/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'cage_ids':
            ( (0,1,1,1,2,2,3,3,3,3),
                (0,0,0,1,1,2,4,4,3,5),
                (0,0,6,6,1,1,1,4,3,5),
                (6,6,6,7,1,8,8,8,5,5),
                (6,9,6,7,8,8,8,10,10,11),
                (9,9,7,7,7,8,10,10,10,11),
                (9,9,7,7,7,12,12,10,10,11),
                (13,13,7,14,14,12,12,10,15,11),
                (13,13,13,14,14,12,15,15,15,15),
                (13,13,12,12,12,12,15,15,15,15)),

            'instance':
            (   (6,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,4),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,7,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0)),
            'width': 10}
    print(solve_puzzle_hanare(**pars))
