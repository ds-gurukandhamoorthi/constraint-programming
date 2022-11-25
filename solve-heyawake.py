import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, rows_and_cols, inside_board
from more_itertools import pairwise
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 1, 0

def solve_puzzle_heyawake(*, height, width, cage_ids, cage_counts):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

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

    adjacency_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            cnstrnt = Not(And(cell_1 == BLACK, cell_2 == BLACK))
            adjacency_c.append(cnstrnt)

    white_stripe_two_region_max_c = []

    # The logic used here is very similar to solve-doppelblock.py
    for cg_id_line, line in zip(rows_and_cols(cage_ids), rows_and_cols(board)):
        rle = [ len(list(g)) for _, g in itertools.groupby(cg_id_line) ]
        window_lengths = [ 2 + run for run in rle ]
        start = 0
        # extend the line for ease of expressing the constraint on windows
        var_line = [BLACK] + list(line) + [BLACK]
        for win_len in window_lengths:
            vars_ = var_line[ start:start+win_len ]
            all_white_in_between = And([ cell == WHITE
                    for cell in vars_[1:-1] ])
            one_delimiter_is_black = Or(vars_[0] == BLACK, vars_[-1] == BLACK)

            # This would disallow white cells spawning to more than one region in a line.
            cnstrnt = Implies(all_white_in_between, one_delimiter_is_black)
            white_stripe_two_region_max_c.append(cnstrnt)
            start = start + win_len - 2

    # CONNECTIVITY of white cells

    range_num_c = []
    # We assign number to each cell in the loop.
    num_board = IntMatrix('num', nb_rows=height, nb_cols=width)
    for row, num_row in zip(board, num_board):
        for cell, num in zip(row, num_row):
            cnstrnt = (cell == BLACK) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (cell == WHITE) == (num >= 0)
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

    s.add( range_c + cage_count_c + adjacency_c + white_stripe_two_region_max_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Heyawake/007.a.htm by author Koyoppz
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'cage_counts': [-1,1,-1,0,-1,1,-1,-1,-1,1,-1,0,-1,1,0,-1,1,-1,-1,-1,3,-1,1,-1,1,-1],
            'cage_ids':
            (   (0,0,1,1,2,2,3,4,4,5),
                (0,0,1,1,2,2,3,4,4,5),
                (6,7,1,1,8,8,8,4,4,5),
                (6,7,9,9,9,10,10,11,12,12),
                (6,7,9,9,9,10,10,11,12,12),
                (13,13,14,15,15,16,16,16,17,18),
                (13,13,14,15,15,16,16,16,17,18),
                (19,20,20,21,21,21,22,22,17,18),
                (19,20,20,23,24,24,22,22,25,25),
                (19,20,20,23,24,24,22,22,25,25)),
            'width': 10}
    solve_puzzle_heyawake(**pars)
