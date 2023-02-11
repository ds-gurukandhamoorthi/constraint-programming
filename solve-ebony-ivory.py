import itertools
from more_itertools import windowed
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, rows_and_cols

BLACK, WHITE = 1, 0

def solve_puzzle_ebony_ivory(*, height, width, horizontal_black_maxruns, horizontal_white_maxruns, vertical_black_maxruns, vertical_white_maxruns):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)
    pars = {'board': board, 'width': width, 'height': height}

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]


    black_maxruns = vertical_black_maxruns + horizontal_black_maxruns
    white_maxruns = vertical_white_maxruns + horizontal_white_maxruns

    do_not_exceed_run_c = []

    for line, b_mxrn in zip(rows_and_cols(board), black_maxruns):
        for longer_window in list(windowed(line, b_mxrn + 1)):
            all_black = And([cell == BLACK for cell in longer_window ])
            cnstrnt = Not(all_black)
            do_not_exceed_run_c.append(cnstrnt)

    for line, b_mxrn in zip(rows_and_cols(board), white_maxruns):
        for longer_window in list(windowed(line, b_mxrn + 1)):
            all_white = And([cell == WHITE for cell in longer_window ])
            cnstrnt = Not(all_white)
            do_not_exceed_run_c.append(cnstrnt)

    # given longest run is reached at least once
    given_run_c = []

    for line, b_mxrn in zip(rows_and_cols(board), black_maxruns):
        possibs = []
        for window in list(windowed(line, b_mxrn)):
            all_black_wndw = And([cell == BLACK for cell in window ])
            possibs.append(all_black_wndw)
        cnstrnt = Or(possibs)
        given_run_c.append(cnstrnt)

    for line, b_mxrn in zip(rows_and_cols(board), white_maxruns):
        possibs = []
        for window in list(windowed(line, b_mxrn)):
            all_white_wndw = And([cell == WHITE for cell in window ])
            possibs.append(all_white_wndw)
        cnstrnt = Or(possibs)
        given_run_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + do_not_exceed_run_c + given_run_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Ebony-Ivory/007.a.htm by author Mikhail Khotiner
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 15,
            'horizontal_black_maxruns': [5, 4, 6, 7, 4, 2, 2, 2, 3, 2, 1, 7, 3, 1, 7],
            'horizontal_white_maxruns': [9, 3, 6, 4, 4, 4, 3, 3, 3, 4, 5, 3, 6, 7, 7],
            'vertical_black_maxruns': [5, 1, 2, 9, 2, 1, 7, 5, 3, 2, 3, 2, 10, 7, 2],
            'vertical_white_maxruns': [8, 7, 7, 3, 12, 12, 4, 3, 3, 7, 7, 7, 3, 2, 12 ],
            'width': 15}
    solve_puzzle_ebony_ivory(**pars)

