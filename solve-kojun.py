import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, inside_board, rows_and_cols, transpose
from more_itertools import pairwise

def solve_puzzle_kojun(*, height, width, cage_ids, instance):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

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

    adjacency_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            cnstrnt = cell_1 != cell_2
            adjacency_c.append(cnstrnt)

    vertical_pecking_order_c = []
    for cage_id_row, row in zip(transpose(cage_ids), transpose(board)):
        for (cg_id_1, cg_id_2), (cell_1, cell_2) in zip(pairwise(cage_id_row), pairwise(row)):
            if cg_id_1 == cg_id_2:
                cnstrnt = cell_1 > cell_2
                vertical_pecking_order_c.append(cnstrnt)

    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(height), range(width))
            if instance[l][c] > 0 ]

    s = Solver()

    # cage_range_c, cage_elems_distinct_c and instance_c same as for suguru solve-suguru.py.  adjacency constraint is more lenient in Kojun (merely orthogonal instead of in 8-directions)
    s.add( cage_range_c + cage_elems_distinct_c + adjacency_c + instance_c + vertical_pecking_order_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Kojun/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'cage_ids':
            ((0,1,1,1,1,1,2,2),
                (0,0,1,1,3,3,4,4),
                (5,5,6,6,6,6,7,7),
                (5,8,8,9,10,10,11,7),
                (12,8,8,8,10,13,11,11),
                (12,14,8,15,13,13,13,16),
                (12,14,8,15,13,17,18,18),
                (12,12,19,20,20,17,17,17)),
            'instance':
            ( (3,7,5,3,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,1,0,2,0,0,0,0),
                (0,0,0,0,0,1,0,0),
                (0,0,6,4,0,0,0,0),
                (0,0,3,0,3,0,5,0),
                (0,0,0,0,0,0,0,0),
                (0,5,0,0,0,0,4,0),
                ),
            'width': 8}
    solve_puzzle_kojun(**pars)
