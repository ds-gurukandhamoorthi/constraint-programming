import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols

EMPTY = 0

def solve_puzzle_nanbaboru(puzzle, *, height, width, to_be_filled, to_be_left_empty, max_num):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ And( n >= 0, n <= max_num)
            for n in flatten(board) ]

    each_n_exactly_once_c = []
    # This is one way of expressing the constraint. The other way is to use distinct when not equal to 0... (as we did with the id_board idea)
    # This can be also thought of as a loose/sparse latin constraint
    for n in range(1, max_num + 1):
        for line in rows_and_cols(board):
            occurrences_given_number = [ cell == n
                    for cell in line ]
            cnstrnt = Exactly(*occurrences_given_number, 1)
            each_n_exactly_once_c.append(cnstrnt)

    at_ = lambda l, c : board[l][c]

    filled_c = []
    for l, c in to_be_filled:
        cnstrnt = at_(l, c) != EMPTY
        filled_c.append(cnstrnt)

    empty_c = []
    for l, c in to_be_left_empty:
        cnstrnt = at_(l, c) == EMPTY
        empty_c.append(cnstrnt)

    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]


    s = Solver()

    s.add( range_c + each_n_exactly_once_c + filled_c + empty_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Nanbaboru/007.a.htm by author Adolfo Zanellati
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 6,
            'max_num' : 4,
            'to_be_filled': [(3,0), (5,5)],
            'to_be_left_empty': [(1,1), (1, 4), (2,2)],
            'puzzle':
            (   (0,0,0,0,1,0),
                (0,0,0,4,0,0),
                (0,0,0,2,0,0),
                (0,0,0,0,0,0),
                (0,3,2,0,0,1),
                (4,0,0,3,0,0)),
            'width': 6}
    solve_puzzle_nanbaboru(**pars)
