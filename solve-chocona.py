import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, inside_board

BLACK, WHITE = 1, 0

def solve_puzzle_chocona(*, height, width, cage_ids, cage_counts):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    #number of black cells in a cage
    cage_count_c = []

    cages_inds = get_same_block_indices(cage_ids)

    for board_indices, cnt in zip(cages_inds.values(), cage_counts):
        if cnt >= 0:
            vars_ = get_vars_at(board_indices)
            black_cells_in_cage = [ cell == BLACK for cell in vars_ ]
            cnstrnt = Exactly(*black_cells_in_cage, cnt)
            cage_count_c.append(cnstrnt)

    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        black_cells_in_a_square = [ at_(*cell) == BLACK for cell in val_cells_in_square ]
        # The following constraint would in a context-free manner force black areas to be rectangles. And would disallow adjacent rectangle areas.
        return Not(Exactly(*black_cells_in_a_square, 3))

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    rect_adj_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]
    #constraint for both being-rectangular and disallowing orthogonal adjacency

    s = Solver()

    s.add( range_c + cage_count_c + rect_adj_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Chocona/007.a.htm by author Iwa Daigeki
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'cage_counts': [4, 2, 4, 3, 4, 1, 1, 2, -1, 4, 3, 4, 4, 1, 1, 2, 2, 2, 2, 3, 2],
            'cage_ids':
            (  (0,0,1,2,2,2,3,3,3,3),
                (0,0,1,1,2,2,3,3,3,4),
                (5,5,6,6,6,6,3,4,4,4),
                (5,7,7,7,7,7,3,8,9,9),
                (10,10,10,11,11,11,8,8,9,9),
                (10,12,12,11,11,11,8,8,9,9),
                (10,12,12,13,13,8,8,8,9,9),
                (10,10,14,14,14,15,15,16,17,17),
                (18,18,18,18,18,15,15,16,17,17),
                (19,19,19,16,16,16,16,16,20,20)),
            'width': 10}
    solve_puzzle_chocona(**pars)
