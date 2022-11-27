import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, rows_and_cols, inside_board
from more_itertools import pairwise
from puzzles_common import ortho_neighbours as neighbours

EMPTY = 0

def list_contains_count_times_val(lst, *, count, val):
    return Exactly(*[var == val
        for var in lst], count)


def solve_puzzle_nanro(*, height, width, cage_ids, instance):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    # we also force the other elements to be 0. (so as not to have a separate range_c)
    cage_elems_n_n_times_c = []
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        cage_size = len(vars_)
        possibilities = []
        for nb_occur in range(1, cage_size + 1):
            contains_n_n_times = list_contains_count_times_val(vars_, count=nb_occur, val=nb_occur)
            nothing_else = list_contains_count_times_val(vars_, count=cage_size - nb_occur,  val = EMPTY)
            possibilities.append(And(contains_n_n_times, nothing_else))
        cnstrnt = Exactly(*possibilities, 1)
        cage_elems_n_n_times_c.append(cnstrnt)

    adj_cage_c = []
    for line, cg_id_line in zip(rows_and_cols(board), rows_and_cols(cage_ids)):
        for (cell_1, cell_2), (cg_id_1, cg_id_2) in zip(pairwise(line), pairwise(cg_id_line)):
            different_cages = cg_id_1 != cg_id_2
            different_vals = Not(And(cell_1 != EMPTY, cell_2 != EMPTY, cell_1 == cell_2))
            cnstrnt = Implies(different_cages, different_vals)
            adj_cage_c.append(cnstrnt)

    # A square of 4 cells can contain at most 3 numbered cells
    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        numbered_cells_in_square = [ at_(*cell) != EMPTY for cell in val_cells_in_square ]
        return AtMost(*numbered_cells_in_square, 3)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    density_numbers_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]
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

    instance_c = [ at_(l, c) == instance[l][c]
            for l, c in itertools.product(range(height), range(width))
            if instance[l][c] > 0 ]

    s = Solver()

    s.add( cage_elems_n_n_times_c + adj_cage_c + density_numbers_c + connectivity_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Nanro/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 12,
            'instance':
            (  (5,0,0,0,0,0,5,5,3,0,0,0),
                (5,0,0,0,0,0,0,0,0,5,3,0),
                (0,0,0,0,2,0,0,0,0,0,0,0),
                (2,0,5,0,0,0,3,0,0,0,0,0),
                (0,0,4,0,0,0,0,0,0,0,0,0),
                (0,3,0,0,0,3,5,0,0,0,5,5),
                (3,3,0,0,0,0,0,0,0,2,0,0),
                (2,0,4,0,3,0,0,5,0,0,0,5),
                (0,0,0,3,0,0,0,0,0,0,0,0),
                (0,0,3,0,0,0,0,0,0,0,2,0),
                (0,5,0,3,3,0,0,0,2,2,0,3),
                (0,0,5,0,0,5,0,0,0,0,0,3)),
            'cage_ids':
            ( (0,0,0,1,1,1,1,1,2,3,3,3),
                (0,0,0,1,1,4,5,2,2,6,3,3),
                (0,7,7,7,4,4,5,2,2,6,6,8),
                (9,7,7,7,7,5,5,5,6,6,10,8),
                (9,9,11,11,11,11,12,12,6,6,10,8),
                (13,13,13,13,11,14,12,12,12,15,10,10),
                (13,13,16,14,14,14,14,14,12,15,15,10),
                (17,17,16,16,18,18,18,19,19,19,15,10),
                (17,16,16,20,18,18,19,19,19,21,10,10),
                (22,22,20,20,20,20,23,19,24,21,21,21),
                (22,22,20,25,25,23,23,23,24,24,26,26),
                (22,22,22,25,25,23,23,23,23,24,26,26)),
            'width': 12}
    solve_puzzle_nanro(**pars)
