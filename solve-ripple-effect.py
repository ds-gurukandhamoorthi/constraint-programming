import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, get_same_block_indices
from more_itertools import windowed

def solve_puzzle_ripple_effect(*, height, width, cage_ids, instance):
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

    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(height), range(width))
            if instance[l][c] > 0 ]

    # 1?1   ? = not 1
    # 2??2  ? = not 2
    # 3???3 ? = not 3
    # can be expressed as in any block of 2 contiguous elements '..' there is at most a single 1; in any block of 3 contiguous elements '...' there is at most a single 2 etc
    adjacency_c = []
    for n in range(1, max_cage_size + 1):
        for row in board:
            for contig_blk in windowed(row, n+1):
                cnstrnt = AtMost(*[cell == n for cell in contig_blk], 1)
                adjacency_c.append(cnstrnt)
        for col in transpose(board):
            for contig_blk in windowed(col, n+1):
                cnstrnt = AtMost(*[cell == n for cell in contig_blk], 1)
                adjacency_c.append(cnstrnt)

    s = Solver()

    s.add( cage_range_c + cage_elems_distinct_c + instance_c + adjacency_c )

    s.check()
    m = s.model()

    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    pars = {'height': 10,
            'cage_ids': 
            ( (0,1,2,2,3,3,3,3,4,4),
                (0,5,5,6,6,6,7,3,4,4),
                (0,8,5,5,5,9,9,3,10,4),
                (0,11,5,12,12,12,13,3,14,14),
                (15,11,11,16,17,18,13,13,13,13),
                (19,11,11,17,17,17,20,20,20,21),
                (19,22,11,23,24,24,24,24,20,21),
                (19,25,25,26,26,26,27,24,20,21),
                (19,28,25,25,25,29,27,24,30,21),
                (31,28,25,32,32,32,32,24,30,33) ),
            'instance':
            ( (0,0,0,0,5,4,0,0,1,0),
                (0,0,0,0,0,0,0,0,0,3),
                (0,0,0,1,3,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,3,0,0,0,0,4,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,6,0,0,4),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,2,0,0,0,0,0,3),
                (0,0,0,0,0,4,0,0,0,0) ),
            'width': 10}
    solve_puzzle_ripple_effect(**pars)
