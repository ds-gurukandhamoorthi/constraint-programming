import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose
from collections import defaultdict

WHITE, BLACK = 0, 1

# We group by content. all cells containing 0 for example
def get_same_block_indices(matrix):
    res = defaultdict(list)
    for l, row in enumerate(matrix):
        for c, val in enumerate(row):
            res[val].append((l, c))
    return res

def solve_puzzle_tairupeinto(*, height, width, cage_ids, vertical_counts, horizontal_counts):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [Xor( clr == WHITE, clr == BLACK )for clr in flatten(board)]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    #same color in each region/cage
    homogenous_cage_color_c = []
    cage_range_c = []
    cage_elems_distinct_c = []
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        all_black = And([cell == BLACK for cell in vars_])
        all_white = And([cell == WHITE for cell in vars_])
        cnstrnt = Xor(all_white, all_black)
        homogenous_cage_color_c.append(cnstrnt)

    # vertical counts means number of tents in each row. Noted vertically on the board
    # on the left or right side
    assert len(vertical_counts) == height == len(board)
    row_sums_c = [ Exactly(*[cell == BLACK for cell in row], count_v)
            for row, count_v in zip(board, vertical_counts) ]

    row_sums_c = []
    for row, count_v in zip(board, vertical_counts):
        if count_v >= 0:
            # Note: Sum can be used too.. but it would be too tied to how we represent BLACK and WHITE variables.
            cnstrnt = Exactly(*[cell == BLACK for cell in row], count_v)
            row_sums_c.append(cnstrnt)

    col_sums_c = []
    for col, count_h in zip(transpose(board), horizontal_counts):
        if count_h >= 0:
            cnstrnt = Exactly(*[cell == BLACK for cell in col], count_h)
            col_sums_c.append(cnstrnt)


    s = Solver()

    s.add( range_c + homogenous_cage_color_c + row_sums_c + col_sums_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Tairupeinto/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'cage_ids': 
            (   (0,0,1,1,1,2,2,2,3,3),
                (0,0,4,1,1,1,5,5,3,3),
                (6,7,4,8,8,9,5,5,5,3),
                (6,7,4,8,9,9,9,9,10,10),
                (6,7,4,11,11,12,12,13,13,10),
                (7,7,4,14,14,14,14,13,15,10),
                (7,16,16,17,17,14,14,13,15,10),
                (18,19,19,19,19,19,15,15,15,10),
                (18,18,20,20,20,21,21,22,22,22),
                (18,18,20,20,20,21,21,22,22,22)),
            'vertical_counts': (7, -1, 3, -1, 4, 6, -1, 7, 4, -1),
            'horizontal_counts': (8, 5, -1, -1, 3, -1, -1, -1, -1),
            'width': 10}
    solve_puzzle_tairupeinto(**pars)
