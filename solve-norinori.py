import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, rows_and_cols, inside_board
from more_itertools import windowed
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 1, 0

def solve_puzzle_norinori(*, height, width, cage_ids):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cage_c = []

    cages_inds = get_same_block_indices(cage_ids)
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        black_cells_in_cage = [ cell == BLACK
                for cell in vars_ ]
        cnstnrt = Exactly(*black_cells_in_cage, 2)
        cage_c.append(cnstnrt)

    # disallowing runs (run as in run length encoding) would disallow longer runs too
    disallow_runs_3_black_c = []
    for row in rows_and_cols(board):
        for wnd in windowed(row, 3):
            all_black = coerce_eq(wnd, [BLACK] * 3)
            cnstnrt = Not(all_black)
            disallow_runs_3_black_c.append(cnstnrt)

    disallow_single_black_cells_c = []
    for l, c in itertools.product(range(height), range(width)):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width) ]
        neighs = get_vars_at(val_neighs)
        one_neigh_is_black = Or([ cell == BLACK for cell in neighs ])
        curr_cell = at_(l, c)
        cnstnrt = Implies((curr_cell == BLACK), one_neigh_is_black)
        disallow_single_black_cells_c.append(cnstnrt)

    # domino = stripe of length 2
    # we forbid length >= 3, length == 1
    domino_c = disallow_runs_3_black_c + disallow_single_black_cells_c

    # Disallowing orthogonal adjacency == cells are stripes of width 1
    # Same code as in solve-nuribou.py
    # To describe that black stripes must have a width of 1, we can say any square in the grid can have at most 2 black squares. A black strip of width greater than 1 would have more than 2 black squares in one of the squares.
    black_stripe_c = []

    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        black_cells_in_a_square = [ at_(*cell) == BLACK for cell in val_cells_in_square ]
        # The following constraint would in a context-free manner force black lines to have a length of 1 (stripes).
        return AtMost(*black_cells_in_a_square, 2)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    black_stripe_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    s = Solver()

    s.add( range_c + cage_c + domino_c + black_stripe_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Norinori/007.a.htm by author Iwa Daigeki
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'cage_ids':
            ( (0,1,2,2,3,4,5,5,6,5),
                (0,1,2,2,3,4,4,5,6,5),
                (1,1,1,2,2,2,4,5,5,5),
                (7,7,7,2,4,4,4,9,9,5),
                (7,7,7,8,8,8,10,9,9,9),
                (11,7,8,8,8,8,10,12,12,9),
                (11,7,8,8,8,13,10,9,9,9),
                (14,14,14,14,8,13,10,9,15,15),
                (14,16,16,14,8,8,10,9,9,9),
                (14,14,14,14,17,17,17,9,9,9)),
            'width': 10}
    solve_puzzle_norinori(**pars)
