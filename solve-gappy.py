import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, inside_board
from more_itertools import windowed

BLACK, WHITE = 1, 0

def solve_puzzle_gappy(*, height, width, horizontal_counts, vertical_counts):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    count_black_cells_c = []
    for line in rows_and_cols(board):
        cnstrnt = Exactly(*[cell == BLACK for cell in line], 2)
        count_black_cells_c.append(cnstrnt)

    at_ = lambda l, c : board[l][c]
    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        black_cells_in_a_square = [ at_(*cell) == BLACK for cell in val_cells_in_square ]
        return AtMost(*black_cells_in_a_square, 1)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    adj_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]
    # A "block" being contiguous white cells in a line delimited by black squares/cells
    count_block_c = []

    counts = vertical_counts + horizontal_counts
    for line, cnt in zip(rows_and_cols(board), counts):
        possibs = []
        for wnd in windowed(line, cnt + 2):
            delimited_black = And(wnd[0] == BLACK, wnd[-1] == BLACK)
            # contiguous white cells forming a stripe between the two black cells
            white_in_between = coerce_eq(wnd[1:-1], [WHITE]*cnt)
            possibs.append(And(delimited_black, white_in_between))
        cnstrnt = Exactly(*possibs, 1)
        count_block_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + count_black_cells_c + adj_c + count_block_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Gappy/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'horizontal_counts': [5, 1, 7, 1, 1, 1, 8, 3, 3, 4],
            'vertical_counts':[3, 8, 1, 1, 2, 1, 1, 3, 5, 1],
            'width': 10}
    solve_puzzle_gappy(**pars)
