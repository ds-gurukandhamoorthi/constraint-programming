import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board
from puzzles_common import ortho_neighbours as neighbours


BLACK, WHITE = 1, 0

# input is grid_index, output is index in board
def grid_neighbours(*,grid_index=(0, 0), height, width):
    l, c = grid_index
    neighs = [(l, c), (l - 1, c), (l, c - 1), (l - 1, c - 1)]
    return [ neigh for neigh in neighs
            if inside_board(neigh, height=height, width=width) ]

# Creek
def solve_puzzle_kuriku(*, height, width, neighbours_counts):
    board = IntMatrix('b', nb_rows=height, nb_cols=width)
    pars = {'board': board, 'width': width, 'height': height}

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    adj_black_neighs_c = []

    # The grid has one more row and one more column than the board
    # gl: grid_line, gc: grid_column
    for gl, row in enumerate(neighbours_counts):
        for gc, nb_neighs in enumerate(row):
            if nb_neighs >= 0:
                indices_neighs = grid_neighbours(grid_index=(gl, gc), height=height, width=width)
                neigh_cells = get_vars_at(indices_neighs)
                neigh_black_cells = [cell == BLACK for cell in neigh_cells]
                cnstrnt = Exactly(*neigh_black_cells, nb_neighs)
                adj_black_neighs_c.append(cnstrnt)

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

    s.add( range_c + adj_black_neighs_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Creek/007.a.htm by author Iwa Daigeki
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'neighbours_counts': (
                (-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,),
                (-1,2,0,-1,-1,2,-1,-1,-1,-1,4,2,-1,-1,-1,-1,),
                (-1,-1,-1,3,-1,2,-1,3,-1,-1,-1,-1,3,-1,2,-1,),
                (-1,3,-1,-1,-1,-1,-1,-1,-1,-1,2,1,-1,-1,-1,-1,),
                (-1,1,-1,-1,2,2,2,-1,-1,-1,-1,-1,-1,-1,3,-1,),
                (-1,-1,3,-1,-1,1,-1,3,3,-1,-1,4,-1,-1,-1,-1,),
                (1,-1,-1,-1,3,-1,-1,-1,-1,-1,-1,-1,1,-1,3,-1,),
                (-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1,-1,-1,),
                (-1,-1,3,-1,2,-1,3,3,-1,-1,-1,-1,3,-1,2,-1,),
                (-1,-1,-1,-1,2,-1,-1,-1,3,-1,2,-1,-1,-1,-1,1,),
                (-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,-1,-1,)),
            'width': 15}
    solve_puzzle_kuriku(**pars)

