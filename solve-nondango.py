import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board, get_same_block_indices, rows_and_cols
from more_itertools import windowed

EMPTY, BLACK, WHITE = 0, 1, 2

# including the 'current'/given-as-argument cell-index
def diagonal_strip_slope_neg(index_, *, height, width):
    l, c = index_
    north_west = ((l - l_off , c - c_off)
            for l_off, c_off in zip(range(l+1), range(c+1))
            if c_off != 0 and l_off != 0)
    south_east = ((l_, c_)
            for l_, c_ in zip(range(l+1, height), range(c+1, width)))
    yield index_
    yield from north_west
    yield from south_east

# including the 'current'/given-as-argument cell-index
def diagonal_strip_slope_pos(index_, *, height, width):
    l, c = index_
    north_east = ((l - l_off , c_)
            for l_off, c_ in zip(range(l+1), range(c, width))
            if l_off != 0)
    south_west = ((l_, c - c_off)
            for l_, c_off in zip(range(l, height), range(c+1))
            if c_off != 0)
    yield index_
    yield from north_east
    yield from south_west

def negative_slope_diagonals(*, height, width):
    res = []
    for c in range(width):
        diag = list(diagonal_strip_slope_neg((0, c), height=height, width=width))
        res.append(diag)
    for l in range(height):
        # (0, 0) already taken into account
        if l == 0:
            continue
        diag = list(diagonal_strip_slope_neg((l, 0), height=height, width=width))
        res.append(diag)
    return res

def positive_slope_diagonals(*, height, width):
    res = []
    for c in range(width):
        diag = list(diagonal_strip_slope_pos((0, c), height=height, width=width))
        res.append(diag)
    for l in range(height):
        # (0, width - 1) already taken into account
        if l == 0:
            continue
        diag = list(diagonal_strip_slope_pos((l, width - 1), height=height, width=width))
        res.append(diag)
    return res

def diagonals(matrix, *, height, width):
    res = []
    at_ = lambda l, c : matrix[l][c]
    def get_elems_at(indices):
        return [ at_(*ind) for ind in indices ]
    both_diagonals = negative_slope_diagonals(height=height, width=width) + positive_slope_diagonals(height=height, width=width)
    for diag_indices in both_diagonals:
        res.append(get_elems_at(diag_indices))
    return res

def rows_cols_and_diags(matrix, *, height, width):
    yield from rows_and_cols(matrix)
    yield from diagonals(matrix, height=height, width=width)


def solve_puzzle_nondango(*, height, width, cage_ids, circles):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Or(*[cell == BLACK, cell == WHITE, cell == EMPTY])
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    instance_c = []
    for l, c in itertools.product(range(height), range(width)):
        devoid_of_circle = circles[l][c] == 0
        empty_cell_in_board = at_(l, c)  == EMPTY
        # equivalence (double-implication) takes care of both cases: empty and non-empty
        cnstrnt = devoid_of_circle == empty_cell_in_board
        instance_c.append(cnstrnt)

    cage_c = []

    cages_inds = get_same_block_indices(cage_ids)
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        black_cells_in_cage = [ cell == BLACK
                for cell in vars_ ]
        cnstnrt = Exactly(*black_cells_in_cage, 1)
        cage_c.append(cnstnrt)


    # avoid runs of 3 same color circles in rows, cols, diags
    avoid_runs_3_c = []
    for line in rows_cols_and_diags(board, height=height, width=width):
        for window in list(windowed(line, 3)):
                all_black_wndw = And([cell == BLACK for cell in window ])
                all_white_wndw = And([cell == WHITE for cell in window ])
                cnstnrt = Not(all_black_wndw)
                avoid_runs_3_c.append(cnstnrt)
                cnstnrt = Not(all_white_wndw)
                avoid_runs_3_c.append(cnstnrt)



    s = Solver()

    s.add( range_c + instance_c + cage_c + avoid_runs_3_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Nondango/007.a.htm by author @Dank_Demes
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processed by z3.
    pars = {'height': 8,
            'cage_ids': ( (0,0,0,1,1,1,1,2),
                (0,3,3,4,4,4,2,2),
                (3,3,5,5,5,4,6,2),
                (7,7,8,5,9,9,6,6),
                (7,7,8,9,9,10,10,6),
                (11,11,8,8,12,10,10,13),
                (11,11,12,12,12,14,14,13),
                (15,15,15,15,14,14,13,13)),
            'circles':( 
            (1,1,1,0,1,1,1,0),
            (1,1,1,1,1,1,1,1),
            (0,1,1,0,0,1,1,1),
            (1,1,0,1,1,0,1,0),
            (0,1,0,1,1,0,1,0),
            (0,1,1,0,1,1,1,0),
            (1,1,1,1,0,1,1,1),
            (1,1,0,0,0,1,1,1)),
            'width': 8}
    solve_puzzle_nondango(**pars)

