import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, inside_board

EMPTY = 0

def solve_puzzle_fuzuli(puzzle, *, height, width, order):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ And(cell >= 0, cell <= order)
            for cell in flatten(board) ]

    # all numbers 1..order present exactly once in each row/column
    all_present_once_c = []
    for n in range(1, order + 1):
        for line in rows_and_cols(board):
            given_number_present_once = Exactly(*[ cell == n for cell in line ], 1)
            all_present_once_c.append(given_number_present_once)

    at_ = lambda l, c : board[l][c]

    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        empty_cells_in_a_square = [ at_(*cell) == EMPTY for cell in val_cells_in_square ]
        return AtLeast(*empty_cells_in_a_square, 1)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    adjacency_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]


    s = Solver()

    s.add( range_c + adjacency_c + instance_c + all_present_once_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Fuzuli/007.a.htm by author Adolfo Zanellati
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 6,
            'order': 4,
            'puzzle':
            (
                (1,0,0,0,0,3),
                (0,0,0,0,4,0),
                (0,3,2,0,0,0),
                (0,0,4,0,0,0),
                (2,0,0,3,0,0),
                (0,0,0,4,0,1),

                ),
            'width': 6}
    solve_puzzle_fuzuli(**pars)
