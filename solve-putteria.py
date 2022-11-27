import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols
from more_itertools import pairwise

EMPTY = 0

def solve_puzzle_putteria(*, height, width, cage_ids, to_be_left_empty):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    # we also force the other elements to be 0. (so as not to have a separate range_c)
    cage_size_once_c = [] #n being the size of the cage
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        cage_size = len(vars_)
        contains_cage_size_once = list_contains_count_times_val(vars_, count=1, val=cage_size)
        nothing_else = list_contains_count_times_val(vars_, count=cage_size - 1,  val=EMPTY)
        cnstrnt = And(contains_cage_size_once, nothing_else)
        cage_size_once_c.append(cnstrnt)

    empty_c = []
    for l, c in to_be_left_empty:
        cnstrnt = at_(l, c) == EMPTY
        empty_c.append(cnstrnt)

    max_cage_size = max([ len(inds)
        for inds in cages_inds.values() ])

    distinct_numbers_line_c = []
    for line in rows_and_cols(board):
        for n in range(1, max_cage_size + 1):
            occurrences_n = [ cell == n for cell in line ]
            cnstrnt = AtMost(*occurrences_n, 1)
            distinct_numbers_line_c.append(cnstrnt)

    adj_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            adj_numbered_cells = And(cell_1 > 0, cell_2 > 0)
            adj_c.append( Not(adj_numbered_cells) )

    s = Solver()

    s.add( cage_size_once_c + empty_c + distinct_numbers_line_c + adj_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Putteria/007.a.htm by author @hirose_atsumi
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'cage_ids':
            ( (0,1,2,2,2,2,3,3),
                (4,1,1,5,6,6,6,7),
                (4,1,5,5,8,6,9,7),
                (4,10,10,8,8,6,11,7),
                (12,12,10,8,11,11,11,11),
                (13,12,14,14,15,16,16,16),
                (13,17,14,14,15,16,16,18),
                (17,17,17,14,15,15,18,18)),
            'to_be_left_empty': [(3,4), (4,3)],
            'width': 8}
    solve_puzzle_putteria(**pars)
