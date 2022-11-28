import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose

BLACK, WHITE = 1, 0

def solve_puzzle_kakurasu(*, height, width, horizontal_sums, vertical_sums, horizontal_values, vertical_values):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    coef_sum_c = []

    for sum_, clrs_row in zip(vertical_sums, board):
        cnstrnt = Sum([If(clr == BLACK, coef, 0)
                for clr, coef in zip(clrs_row, horizontal_values)]) == sum_
        coef_sum_c.append(cnstrnt)
    for sum_, clrs_col in zip(horizontal_sums, transpose(board)):
        cnstrnt = Sum([If(clr == BLACK, coef, 0)
                for clr, coef in zip(clrs_col, vertical_values)]) == sum_
        coef_sum_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + coef_sum_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Kakurasu/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 5,
            'horizontal_sums': [7, 3, 5, 7, 4], 
            'vertical_sums': [10, 6, 6, 4, 4], 
            'horizontal_values': [1, 2, 3, 4, 5], #coefficient-like
            'vertical_values': [1, 2, 3, 4, 5],
            'width': 5}
    solve_puzzle_kakurasu(**pars)
