import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, get_same_block_indices, inside_board
from more_itertools import pairwise
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 1, 0

def solve_puzzle_usoone(puzzle, *, height, width, cage_ids):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    instance_c = [ at_(l, c) != BLACK
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] >= 0 ]

    adj_c = []
    for clrs in rows_and_cols(board):
        for (c1, c2) in pairwise(clrs):
            both_black = And(c1 == BLACK, c2 == BLACK)
            cnstrnt = Not(both_black)
            adj_c.append(cnstrnt)

    cages_inds = get_same_block_indices(cage_ids)

    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    clue_at_ = lambda l, c : puzzle[l][c]

    # one clue exactly is wrong count
    cage_clue_c = []

    def gen_count_neighbours_constraints(n, l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        val_neigh_cells = [at_(*cell) for cell in val_neighs]
        cnstrnt = Exactly(*[cell == BLACK
            for cell in val_neigh_cells], n)
        return cnstrnt

    for board_indices in cages_inds.values():
        board_indices_with_clues = [ indx
                for indx in board_indices
                if clue_at_(*indx) >= 0 ]
        clues = [ clue_at_(*indx) for indx in board_indices_with_clues ]
        # abiding clues: clues and the count of neighbours are in accordance. (not wrong)
        abiding_clues = []
        for indx, clue in zip(board_indices_with_clues, clues):
            cnstrnt = gen_count_neighbours_constraints(clue, *indx)
            abiding_clues.append(cnstrnt)
        nb_clues_in_cage = len(board_indices_with_clues)
        assert nb_clues_in_cage >= 1, "As per the rules of the game, each cage/region contains exactly one wrong clue"
        ONE_WRONG_CLUE = 1
        cnstrnt = Exactly(*abiding_clues, nb_clues_in_cage - ONE_WRONG_CLUE)
        cage_clue_c.append(cnstrnt)

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

    s.add( range_c + instance_c + adj_c + cage_clue_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Usoone/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'puzzle':
            ( (0,-1,2,-1,2,-1,2,-1),
                (-1,-1,-1,1,1,-1,3,-1),
                (-1,0,2,2,-1,2,-1,-1),
                (1,2,-1,2,2,1,1,-1),
                (1,-1,1,-1,3,-1,0,-1),
                (-1,2,-1,-1,-1,3,-1,1),
                (-1,-1,-1,2,-1,-1,3,-1),
                (1,-1,-1,-1,2,-1,-1,0)),
            'cage_ids':
            ( (0,0,1,1,1,2,2,2),
                (0,0,1,1,1,2,2,2),
                (0,0,3,3,3,2,2,2),
                (4,4,4,5,5,6,6,7),
                (4,4,4,8,8,6,6,7),
                (9,9,10,10,10,10,10,7),
                (9,9,10,10,10,10,10,11),
                (9,9,10,10,10,10,10,11)),
            'width': 8}
    solve_puzzle_usoone(**pars)
