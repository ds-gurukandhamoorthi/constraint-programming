import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, inside_board
from more_itertools import pairwise
from puzzles_common import ortho_neighbours as neighbours

EMPTY = 0

def solve_puzzle_sukoro(puzzle, *, height, width):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ And( n >= 0, n <= 4)
            for n in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]

    adj_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            # If two adjacent cells not empty ( contains a number >= 1) then those two numbers must be different
            not_empty = And(cell_1 > 0, cell_2 > 0)
            cnstrnt = Implies(not_empty, cell_1 != cell_2)
            adj_c.append( cnstrnt )

    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    def gen_count_neighbours_constraint(l, c):
        geom = { 'height': height, 'width': width }
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, **geom) ]
        neighs = get_vars_at(val_neighs)
        count_var = at_(l, c) #content of current cell: count of neighbours
        cnstrnts =  []
        for n in range(1, 4 + 1):
            n_neighbours = Exactly( *[ adj != EMPTY for adj in neighs ], n )
            # If we write 'bi-implication' here, we need to take into account empty cells... A cell can have 3 non-empty neighbours and not have a count of 3 (because it's empty)
            cnstrnts.append(Implies(count_var == n, n_neighbours))
        return And(cnstrnts)

    # constraint coercing number of adjacent numbered cells to be of the count found in the current cell.
    count_neighbours_c = [ gen_count_neighbours_constraint(l, c)
            for l, c in itertools.product(range(height), range(width)) ]

    # CONNECTIVITY of numbered cells

    range_num_c = []
    # We assign number to each cell in the loop.
    num_board = IntMatrix('num', nb_rows=height, nb_cols=width)
    for row, num_row in zip(board, num_board):
        for cell, num in zip(row, num_row):
            cnstrnt = (cell == EMPTY) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (cell != EMPTY) == (num >= 0)
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

    s.add( range_c + adj_c + count_neighbours_c + instance_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Sukoro/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'puzzle':
            ( (0,3,0,0,1,0,3,0),
                (0,0,3,0,0,0,2,0),
                (0,0,0,0,0,0,3,2),
                (0,0,2,0,1,0,2,0),
                (1,0,0,0,0,0,0,0),
                (0,0,0,0,2,3,0,0),
                (0,0,0,0,0,0,0,1),
                (0,1,2,0,0,1,0,0) ),
            'width': 8}
    solve_puzzle_sukoro(**pars)
