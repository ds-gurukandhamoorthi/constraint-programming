import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, rows_and_cols, inside_board
from more_itertools import windowed
from puzzles_common import ortho_neighbours as neighbours


BLACK, WHITE = 1, 0

def solve_puzzle_aqre(*, height, width, cage_ids, cage_counts):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    #number of black cells in a cage
    cage_count_c = []

    cages_inds = get_same_block_indices(cage_ids)

    for board_indices, cnt in zip(cages_inds.values(), cage_counts):
        if cnt >= 0:
            vars_ = get_vars_at(board_indices)
            black_cells_in_cage = [ cell == BLACK for cell in vars_ ]
            cnstrnt = Exactly(*black_cells_in_cage, cnt)
            cage_count_c.append(cnstrnt)

    # run as in run-length-encoding
    runs_of_3_atmost_c = []
    for line in rows_and_cols(board):
        for wnd in windowed(line, 4):
            all_black = coerce_eq(wnd, [BLACK] * 4)
            all_white = coerce_eq(wnd, [WHITE] * 4)
            all_of_same_color = Or(all_black, all_white)
            # runs of 4 cannot be of same color
            cnstrnt = Not(all_of_same_color)
            runs_of_3_atmost_c.append(cnstrnt)

    # CONNECTIVITY of black cells

    range_num_c = []
    # We assign number to each cell in the loop.
    num_board = IntMatrix('num', nb_rows=height, nb_cols=width)
    for row, num_row in zip(board, num_board):
        for cell, num in zip(row, num_row):
            cnstrnt = (cell == WHITE) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (cell == BLACK) == (num >= 0)
            range_num_c.append(cnstrnt)

    nums = flatten(num_board)
    single_start_c = [ Exactly(*[n == 0 for n in nums], 1) ]


    num_at_ = lambda l, c: num_board[l][c]
    def gen_predecessor_constraints(l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        # the current cell
        cell = num_at_(l,c)
        val_neigh_cells = [num_at_(*cell) for cell in val_neighs]
        one_neigh_is_predecessor = AtLeast(*[And(neigh_cell >= 0, neigh_cell == cell - 1) for neigh_cell in val_neigh_cells], 1)
        cnstrnt = (cell > 0) == one_neigh_is_predecessor
        return cnstrnt


    predecessor_c = [ gen_predecessor_constraints(l, c)
        for l, c in itertools.product(range(height), range(width)) ]

    # connectivity constraint as proposed by Gerhard van der Knijff in 'Solving and generating puzzles with a connectivity constraint'
    # This can be thought of as a creative use of proof-by-induction and Peano's way of definining natural numbers...
    # Some seed/start ... then everything spawns from it.
    connectivity_c = range_num_c + single_start_c + predecessor_c

    s = Solver()

    s.add( range_c + cage_count_c + runs_of_3_atmost_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Aqre/001.a.htm by author @SP1_winter
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 6,
            'cage_ids':
            ( (0,0,0,0,0,0),
                (0,0,0,0,0,0),
                (0,1,1,0,0,0),
                (0,1,0,2,2,0),
                (0,0,0,0,2,0),
                (0,0,0,0,0,0)),
            'cage_counts': [11, 1, 1],
            'width': 6}
    solve_puzzle_aqre(**pars)
