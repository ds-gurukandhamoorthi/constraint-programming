import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board, get_same_block_indices, rows_and_cols
from more_itertools import pairwise

# BLACK = filled with mercury, WHITE = empty visible glass
BLACK, WHITE = 1, 0
MERCURY = BLACK
GLASS = WHITE

def solve_puzzle_thermometer(*, height, width, horizontal_counts, vertical_counts, cage_ids, cage_orientations):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    thermometer_c = []

    cages_inds = get_same_block_indices(cage_ids)

    for cage_id, indices in cages_inds.items():
        thermometer = sorted(indices)
        thermometer_orientation = cage_orientations[cage_id]
        # we want mercury part at the start of the list.
        if thermometer_orientation in '^<':
            thermometer = list(reversed(thermometer))
        thermometer_vars = get_vars_at(thermometer)
        for mercury_side_cell, glass_side_cell in pairwise(thermometer_vars):
            cnstrnt = Implies(glass_side_cell == MERCURY, mercury_side_cell == MERCURY)
            thermometer_c.append(cnstrnt)
            cnstrnt = Implies(mercury_side_cell == GLASS, glass_side_cell == GLASS)
            thermometer_c.append(cnstrnt)

    counts = vertical_counts + horizontal_counts

    count_c = []
    for line, cnt in zip(rows_and_cols(board), counts):
        occupied_cells = [ c == BLACK for c in line ]
        cnstrnt = Exactly(*occupied_cells, cnt)
        count_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + thermometer_c + count_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Thermometer/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'horizontal_counts': [4, 1, 5, 7, 7, 6, 3, 3],
            'vertical_counts': [6, 4, 3, 5, 4, 2, 7, 5],
            'cage_ids': ( (0,1,2,3,3,3,3,3),
            (0,1,2,4,4,5,6,7),
            (0,1,2,8,8,5,6,7),
            (0,1,2,9,10,5,6,7),
            (0,1,2,9,10,11,6,7),
            (12,13,13,13,10,11,6,7),
            (12,14,14,14,14,11,15,16),
            (17,17,17,17,17,11,15,16)),
            #thermometer orientation (cage_orientations):
            # ^ pointing upwards means mercury at bottom (black cells at bottom)
            # > pointing right means mercury at left (black cells at left)
            'cage_orientations':
            ('^', '^', 'v', '>', '<', '^', '^', '^', '>', 'v', 'v',  '^', 'v', '>', '>', '^', 'v', '<'),

            'width': 8}
    solve_puzzle_thermometer(**pars)

