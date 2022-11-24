import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board, rows_and_cols

def solve_puzzle_grades(puzzle, *, height, width, horizontal_counts, vertical_counts, horizontal_sums, vertical_sums):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    s = Solver()

    counts = vertical_counts + horizontal_counts
    sums = vertical_sums + horizontal_sums

    range_c = [ And(n >= 0, n <= max(sums))
            for n in flatten(board) ]

    at_ = lambda l, c : board[l][c]

    # Two numbered cells cannot be adjacent.
    # Adjacency: 8 directions. (think: King's move in chess).
    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        numbered_cells_in_a_square = [ at_(*cell) > 0 for cell in val_cells_in_square ]
        return AtMost(*numbered_cells_in_a_square, 1)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    adjacency_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    count_c = []
    for line, cnt in zip(rows_and_cols(board), counts):
        numbered_cells = [ n > 0 for n in line ]
        cnstrnt = Exactly(*numbered_cells, cnt)
        count_c.append(cnstrnt)

    sum_c = []
    for line, ttl in zip(rows_and_cols(board), sums):
        cnstrnt = Sum(line) == ttl
        sum_c.append(cnstrnt)

    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]

    s.add( range_c + adjacency_c + count_c + sum_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Grades/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'horizontal_counts': [2,1,1,2,2,1,2,1],
            'vertical_counts': [1,2,1,2,1,3,1,1],
            'horizontal_sums': [6,6,9,15,9,3,11,7],
            'vertical_sums': [3,12,6,14,1,17,5,8],
            'puzzle':
            (  (0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,0,0,0,0,3,0,0),
                (0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0)),
            'width': 8}
    solve_puzzle_grades(**pars)
