import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols
from more_itertools import windowed

BLACK = 0

def solve_puzzle_doppelblock(*, height, width, order, vertical_sums, horizontal_sums):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    s = Solver()

    range_c = [ And(cell >= 0, cell <= order)
            for cell in flatten(board) ]

    count_black_cells_c = []
    for line in rows_and_cols(board):
        cnstrnt = Exactly(*[cell == BLACK for cell in line], 2)
        count_black_cells_c.append(cnstrnt)

    def get_id(l, c):
        return -(l * width + c + 1)

    id_board = [[get_id(l, c) for c in range(width)]
            for l in range(height)]

    distinct_c = []
    for line, id_line in zip(rows_and_cols(board), rows_and_cols(id_board)):
        # we replace 0 with `id` of the cell. This is merely to get distinct_when_not_zero
        cnstrnt = Distinct( [If(cell > 0, cell, id_) for cell, id_ in zip(line, id_line) ] )
        distinct_c.append(cnstrnt)

    # A "block" being contiguous white cells in a line delimited by black squares/cells
    sum_block_c = []
    sums = vertical_sums + horizontal_sums # rows add up to clues(sums) noted vertically...
    for line, sum_ in zip(rows_and_cols(board), sums):
        max_len = len(line) # so as to distinguish between rows and cols
        for block_len in range(max_len - 2 + 1):
            for wnd in windowed(line, block_len + 2):
                black_cells_at_both_extremities = wnd[0] == wnd[-1]
                if block_len == 0:
                    # we don't need this condition if we exploit convention Sum([]) = 0
                    cnstrnt = Implies(black_cells_at_both_extremities, (sum_ == 0))
                else:
                    cnstrnt = Implies(black_cells_at_both_extremities, (Sum(wnd[1:-1]) == sum_))
                sum_block_c.append(cnstrnt)



    s.add( range_c + count_black_cells_c + distinct_c + sum_block_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Doppelblock/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 6,
            'order': 4,
            'vertical_sums': [0, 4, 7, 0, 1, 4], #noted vertically on the puzzle left or right
            'horizontal_sums': [0, 10, 0, 4, 1, 0],
            'width': 6}
    solve_puzzle_doppelblock(**pars)
