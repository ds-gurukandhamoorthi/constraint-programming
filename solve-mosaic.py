import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq
from puzzles_common import flatten, inside_board

# We need count of black squares: so BLACK=1
WHITE, BLACK = 0, 1

# disk: all cells (including the center cell included)
# here convention: radius = 0 returns merely the center cell
def cells_in_disk(index_, radius=1):
    l, c = index_
    cells = itertools.product(range(-radius + l, radius + l + 1),
            range(-radius + c, radius + c + 1))
    return list(cells)


def solve_puzzle_mosaic(counts, *, height, width):
    board = IntMatrix('b', nb_rows=height, nb_cols=width)
    at_ = lambda l, c: board[l][c]

    # There is no empty cell:
    complete_c = [ Xor(cell == WHITE, cell == BLACK)
            for cell in flatten(board) ]

    def valid_cells_in_disk(l, c):
        geom = { 'height': height, 'width': width }
        cells = cells_in_disk((l, c), radius=1)
        return [ cell for cell in cells
                if inside_board(cell, **geom) ]

    def gen_sing_count_const(l, c):
        cell_vars = [ at_(*cell) for cell in valid_cells_in_disk(l, c) ]
        # If we don't use sum we may express the constraint with `Exactly()`
        return Sum(cell_vars) == counts[l][c]

    count_c = [ gen_sing_count_const(l, c)
            for l, c in itertools.product(range(height), range(width))
            if counts[l][c] > 0 ]

    s = Solver()
    s.add(complete_c + count_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board]

if __name__ == "__main__":
    pars = {
            'counts':
            [[4, 0, 0, 2, 0, 0], [0, 0, 2, 0, 2, 0], [5, 5, 3, 0, 0, 3], [0, 0, 0, 0, 0, 0]],
            'height': 4,
            'width': 6,
            }

    solve_puzzle_mosaic(**pars)

    pars = {
            'counts':
            [[0, 0, 0, 3, 0, 2, 0, 0, 0, 2, 0, 0, 4, 0, 3],
                [0, 6, 6, 0, 5, 0, 2, 2, 0, 0, 0, 5, 0, 0, 0],
                [3, 0, 0, 6, 5, 4, 3, 0, 4, 0, 0, 3, 0, 0, 4],
                [2, 0, 6, 6, 0, 0, 6, 6, 0, 7, 0, 0, 4, 0, 0],
                [0, 0, 7, 0, 6, 5, 0, 0, 6, 0, 4, 4, 0, 0, 1],
                [0, 5, 0, 0, 0, 6, 9, 0, 0, 0, 7, 0, 5, 3, 0],
                [0, 6, 0, 0, 0, 6, 0, 7, 0, 5, 0, 0, 0, 4, 1],
                [0, 4, 5, 0, 6, 5, 7, 7, 0, 7, 7, 7, 4, 0, 0],
                [3, 0, 0, 5, 6, 0, 0, 7, 0, 6, 0, 0, 0, 0, 3],
                [0, 1, 0, 2, 0, 0, 7, 7, 6, 0, 4, 5, 4, 0, 2],
                [0, 0, 4, 0, 3, 4, 0, 7, 0, 4, 0, 0, 7, 0, 3],
                [0, 3, 0, 4, 0, 3, 0, 0, 0, 0, 4, 4, 0, 3, 0],
                [2, 0, 5, 0, 2, 0, 0, 5, 0, 0, 3, 4, 5, 0, 0],
                [0, 4, 5, 6, 0, 0, 0, 0, 0, 0, 2, 2, 4, 7, 0],
                [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 6, 0]],
            'height': 15,
            'width': 15,
            }
    solve_puzzle_mosaic(**pars)
