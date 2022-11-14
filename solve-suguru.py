import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board
from collections import defaultdict

# We group by content. all cells containing 0 for example
def get_same_block_indices(matrix):
    res = defaultdict(list)
    for l, row in enumerate(matrix):
        for c, val in enumerate(row):
            res[val].append((l, c))
    return res

def solve_puzzle_suguru(*, height, width, cage_ids, instance):
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

    # Two numbers that are adjacent must be different.
    # Adjacency: 8 directions. (think: King's move in chess).
    def gen_proximity_constraints(n, l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        given_num_in_a_square = [ at_(*cell) == n for cell in val_cells_in_square ]
        return AtMost(*given_num_in_a_square, 1)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    adjacency_c = [ gen_proximity_constraints(n, l, c)
        for n, l, c in itertools.product(range(1, max_cage_size + 1), range(height - 1), range(width - 1)) ]

    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(height), range(width))
            if instance[l][c] > 0 ]

    s = Solver()

    s.add( cage_range_c + cage_elems_distinct_c + adjacency_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    pars = {'height': 10,
            'cage_ids':
            (   (0,0,0,1,1,2,2,3,4,4,5,5),
                (0,0,1,1,2,2,3,3,4,5,5,6),
                (7,8,8,1,2,3,3,4,4,5,6,6),
                (7,7,8,8,9,9,9,9,10,10,6,6),
                (11,7,7,8,12,12,12,9,13,10,10,14),
                (11,11,11,11,12,12,15,15,13,13,10,14),
                (16,17,18,19,19,20,20,15,15,13,13,14),
                (16,17,18,18,19,19,20,20,15,21,14,14),
                (16,17,17,18,18,19,22,20,21,21,23,23),
                (16,16,17,22,22,22,22,21,21,23,23,23)
                ),
            'instance':
            (   (0,0,2,0,0,0,1,0,5,0,0,0),
                (1,0,0,0,0,0,0,0,0,0,0,0),
                (0,0,0,4,0,0,0,0,0,0,0,0),
                (0,0,2,0,0,0,0,2,1,0,0,5),
                (0,0,0,0,4,0,0,0,0,0,4,0),
                (4,0,0,0,0,0,0,0,2,0,0,0),
                (0,0,2,0,0,0,3,0,0,0,0,0),
                (0,3,0,0,0,0,0,4,0,0,1,0),
                (2,0,0,0,0,0,0,0,0,0,0,0),
                (5,0,0,1,0,5,4,0,4,5,3,0)
                ),
            'width': 12}
    solve_puzzle_suguru(**pars)
