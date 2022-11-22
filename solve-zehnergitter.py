import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board, transpose

def solve_puzzle_zehnergitter(puzzle, *, height, width, horizontal_sums):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ And( n >= 0, n <= 9)
            for n in flatten(board) ]

    at_ = lambda l, c : board[l][c]

    # Forbidding the same number in adjancent cells (diagonally, orthogonally) is the same constraint in solve-tents.py or solve-suguru.py
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
        for n, l, c in itertools.product(range(0, 9 + 1), range(height - 1), range(width - 1)) ]

    distinct_c = [ Distinct(row)
            for row in board ]

    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] >= 0 ]

    sum_c = [ Sum(col) == ttl
            for col, ttl in zip(transpose(board), horizontal_sums) ]

    s = Solver()

    s.add( range_c + adjacency_c + distinct_c + instance_c + sum_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Zehnergitter/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 5,
            'horizontal_sums': (25, 8, 27, 16, 24, 20, 28, 31, 25, 21),
            'puzzle':
            (   (9,1,5,0,-1,6,4,-1,-1,8),
                (-1,0,-1,1,5,2,7,8,4,-1),
                (3,-1,8,-1,0,4,-1,9,5,1),
                (-1,-1,-1,-1,-1,-1,-1,4,6,-1),
                (2,4,5,6,9,-1,3,-1,-1,0)),
            'width': 10}
    solve_puzzle_zehnergitter(**pars)
