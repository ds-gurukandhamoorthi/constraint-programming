import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board, rows_and_cols
from puzzles_common import ortho_neighbours as neighbours
from more_itertools import windowed

CIRCLE, EMPTY = 1, 0


def solve_puzzle_fobidoshi(puzzle, *, height, width):
    # c stands here for circle instead of color
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == CIRCLE, cell == EMPTY)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    instance_c = [ at_(l, c) == CIRCLE
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] == CIRCLE ]
    # we've used CIRCLE == 1 in both puzzle and board.
    # It's only in absence-of-circle that there is ambiguity: in board 0 = empty. in puzzle 0 = unknown.

    # CONNECTIVITY of cells containing circle

    range_num_c = []
    # We assign number to each cell in the loop.
    num_board = IntMatrix('num', nb_rows=height, nb_cols=width)
    for row, num_row in zip(board, num_board):
        for cell, num in zip(row, num_row):
            cnstrnt = (cell == EMPTY) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (cell == CIRCLE) == (num >= 0)
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

    # avoid runs of 4 circles in rows, cols
    avoid_runs_4_c = []
    for line in rows_and_cols(board):
        for window in list(windowed(line, 4)):
                all_circle_wndw = And([cell == CIRCLE for cell in window ])
                cnstnrt = Not(all_circle_wndw)
                avoid_runs_4_c.append(cnstnrt)

    s = Solver()

    s.add( range_c + instance_c + connectivity_c + avoid_runs_4_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Fobidoshi/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processed by z3.
    pars = {'height': 8,
            'puzzle': 
            #In the end board (variables) 1 = circle 0 = absence of circle
            #but convention used here: 1 = circle, 0 = unknown (if we use -1 for unknown to be consistent with board-of-variables it would add visual clutter).
            ( (1,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,1),
                (1,0,1,0,0,0,1,0),
                (0,0,0,0,0,0,0,1),
                (1,0,0,1,0,0,1,0),
                (0,0,0,0,0,1,0,1),
                (1,0,0,0,1,0,1,0),
                (0,0,0,0,1,1,0,1)),
            'width': 8}
    solve_puzzle_fobidoshi(**pars)

