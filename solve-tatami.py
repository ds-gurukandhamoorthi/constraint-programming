import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices
from more_itertools import pairwise

def solve_puzzle_tatami(*, order, max_num, cage_ids, instance):
    board = IntMatrix('n', nb_rows=order, nb_cols=order)

    range_c = [ And( n >= 0, n <= max_num)
            for n in flatten(board) ]

    nb_occur = order // max_num
    equal_number_occurences = []
    for n in range(1, max_num + 1):
        for line in rows_and_cols(board):
            occurrences_given_number = [ cell == n
                    for cell in line ]
            cnstrnt = Exactly(*occurrences_given_number, nb_occur)
            equal_number_occurences.append(cnstrnt)

    adj_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            cnstrnt = cell_1 != cell_2
            adj_c.append( cnstrnt )

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    max_cage_size = 0
    cage_range_c = []
    cage_elems_distinct_c = []
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        cage_size = len(vars_)
        max_cage_size = max(cage_size, max_cage_size)
        cnstrnts = [ And(var >= 1, var <= cage_size) for var in vars_ ]
        cage_range_c.extend(cnstrnts)
        cage_elems_distinct_c.append(Distinct(vars_))

    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(order), range(order))
            if instance[l][c] > 0 ]

    s = Solver()

    s.add( range_c + equal_number_occurences + adj_c + cage_range_c + cage_elems_distinct_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Patchwork/007.a.htm by author Adolfo Zanellati
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'order': 8,
            'max_num' : 4,
            'cage_ids':
            ( (0,0,0,0,1,1,1,1),
                (2,3,4,4,4,4,5),
                (2,3,7,7,7,7,5),
                (2,3,8,8,8,8,5),
                (2,3,9,9,9,9,5),
                (10,10,10,10,11,11,11,11),
                (12,12,12,12,13,13,13,13),
                (14,14,14,14,15,15,15,15)),
            'instance':
            ((0,0,0,2,3,0,0,0),
                (0,0,1,0,0,0,2,0),
                (0,0,4,0,0,0,0,4),
                (0,4,0,0,0,0,0,0),
                (1,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,0,0,1,0,0,2,1),
                (0,4,0,0,1,0,0,0)),
            }
    solve_puzzle_tatami(**pars)
