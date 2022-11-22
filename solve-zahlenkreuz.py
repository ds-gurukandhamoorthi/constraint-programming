import itertools
from z3 import *
from more_z3 import BoolMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols

def solve_puzzle_zahlenkreuz(puzzle, *, height, width, horizontal_sums, vertical_sums):
    black_board = BoolMatrix('blk', nb_rows=height, nb_cols=width)

    s = Solver()

    sum_c = []
    sums = vertical_sums + horizontal_sums # rows add up to clues(sums) noted vertically...
    for clrs, vals, sum_ in zip(rows_and_cols(black_board), rows_and_cols(puzzle), sums):
        cnstrnt = Sum([If(blk, 0, val) for blk, val in zip(clrs, vals)]) == sum_
        sum_c.append(cnstrnt)

    s.add( sum_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in black_board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Zahlenkreuz/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 5,
            'horizontal_sums': [11, 13, 19, 11, 9],
            'puzzle':
            (  (3,6,4,4,6),
                (6,7,3,5,4),
                (2,9,6,3,1),
                (2,5,9,2,6),
                (2,9,7,3,3) ),
            'vertical_sums': [9, 21, 5, 15, 13],
            'width': 5}
    solve_puzzle_zahlenkreuz(**pars)
    # shows if a cell is black (True) or white (False)
