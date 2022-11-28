import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, inside_board
from more_itertools import pairwise
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 1, 0

# orthogonal neighbours at a given distance
def ortho_dist_neighbours(index_, dist):
    up, down, left, right = (dist, dist, dist, dist)
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]

def solve_puzzle_kuroshuto(puzzle, *, height, width):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    instance_c = [ at_(l, c) != BLACK
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]

    adj_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            cnstrnt = Not(And(cell_1 == BLACK, cell_2 == BLACK))
            adj_c.append( cnstrnt )

    distance_c = []

    def gen_distance_constraint(l, c, dist):
        geom = { 'height': height, 'width': width }
        val_neighs = [ neigh for neigh in ortho_dist_neighbours((l, c), dist)
                if inside_board(neigh, **geom) ]
        neighs = get_vars_at(val_neighs)

        one_cell_at_given_dist_is_black = Exactly(*[ neigh_dist == BLACK for neigh_dist in neighs ], 1)
        return one_cell_at_given_dist_is_black

    # constraint forcing exactly one of the cells at a given distnace to be BLACK
    distance_c = [ gen_distance_constraint(l, c, puzzle[l][c])
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]


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

    s.add( range_c + instance_c + adj_c + distance_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Kuroshuto/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'puzzle':
            (  (0,0,0,0,0,1,4,0,0,0),
                (0,0,2,0,0,0,0,0,0,0),
                (1,0,4,0,0,3,0,0,4,0),
                (0,0,0,0,5,0,4,1,0,0),
                (0,3,0,0,0,3,5,0,0,0),
                (0,0,1,0,0,0,0,0,5,1),
                (0,0,0,1,0,0,1,0,4,0),
                (7,0,4,6,0,0,0,0,0,5),
                (0,0,0,4,0,4,0,0,5,0),
                (5,0,1,2,5,0,0,0,0,0)),
            'width': 10}
    solve_puzzle_kuroshuto(**pars)
