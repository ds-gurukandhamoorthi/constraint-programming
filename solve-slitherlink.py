import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board
from collections import defaultdict
from more_itertools import pairwise

WALL, POROUS = 1, 0
IN_THE_LOOP, OUT_OF_THE_LOOP = 1, 0

def neighbours(index_):
    up, down, left, right = (1, 1, 1, 1)
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]

def solve_puzzle_slitherlink(puzzle, *, height, width):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)
    # left right   |cell|
    lr_walls_board = IntMatrix('lr_w', nb_rows=height, nb_cols=width + 1)
    # top bottom
    tb_walls_board = IntMatrix('tb_w', nb_rows=height + 1, nb_cols=width)

    left_and_right_walls = dict()
    for l, row_var_walls in enumerate(lr_walls_board):
        for c, two_walls in enumerate(pairwise(row_var_walls)):
            left_and_right_walls[(l, c)] = two_walls

    top_and_bottom_walls = dict()
    for c, col_var_walls in enumerate(transpose(tb_walls_board)):
        for l, two_walls in enumerate(pairwise(col_var_walls)):
            top_and_bottom_walls[(l, c)] = two_walls

    walls_at = defaultdict(list)
    for cell in left_and_right_walls:
        walls = left_and_right_walls[cell]
        walls_at [cell].extend(walls)
    for cell in top_and_bottom_walls:
        walls = top_and_bottom_walls[cell]
        walls_at [cell].extend(walls)

    walls_board = list(itertools.chain(lr_walls_board, tb_walls_board))
    range_walls_c = [Xor(border == WALL, border == POROUS)
            for border in flatten(walls_board)]

    count_walls_c = []
    for l, row in enumerate(puzzle):
        for c, wall_count in enumerate(row):
            if wall_count > -1:
                cnstrnt =Exactly(*[w == WALL for w in walls_at[(l, c)]], wall_count)
                count_walls_c.append(cnstrnt)

    range_loop_c = [Xor(border == IN_THE_LOOP, border == OUT_OF_THE_LOOP)
            for border in flatten(board)]

    # NOTE: Perhaps this is a redundant constraint
    permeation_c = []
    for row, walls in zip(board, lr_walls_board):
        # walls[1:-1] we skip the walls at the extremities of the playing-field
        for adj_cells, wall in zip(pairwise(row), walls[1:-1]):
            cnstrnt = Implies(wall == POROUS, adj_cells[0] == adj_cells[1])
            permeation_c.append(cnstrnt)
            cnstrnt = Implies(wall == WALL, adj_cells[0] != adj_cells[1])
            permeation_c.append(cnstrnt)

    def walls_at(l, c):
        for offset in [-1, 0]:
            if 0 <= l+offset < height:
                yield lr_walls_board[l+offset][c]
            if 0 <= c+offset < width:
                yield tb_walls_board[l][c+offset]

    # constraint on degree as proposed by Gerhard van der Knijff in 'Solving and generating puzzles with a connectivity constraint'
    # On this puzzle this can be seen as avoiding isolated walls and 'T' shaped wall formations of three walls.
    degree_c = []
    for l in range(height+1):
        for c in range(width+1):
            cnstrnt = Or(Sum(list(walls_at(l, c))) == 2,
                    Sum(list(walls_at(l, c))) == 0)
            degree_c.append(cnstrnt)

    # CONNECTIVITY of cells inside the loop

    range_num_c = []
    # We assign number to each cell in the loop.
    num_board = IntMatrix('n', nb_rows=height, nb_cols=width)
    for row, num_row in zip(board, num_board):
        for cell, num in zip(row, num_row):
            cnstrnt = (cell == OUT_OF_THE_LOOP) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (cell == IN_THE_LOOP) == (num >= 0)
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


    # "CONNECTIVITY" of cells not belonging to the loop

    out_range_num_c = []
    # We assign number to each cell in the loop.
    out_num_board = IntMatrix('o', nb_rows=height+2, nb_cols=width+2)
    for row, num_row in zip(board, out_num_board[1:-1]):
        for cell, num in zip(row, num_row[1:-1]):
            cnstrnt = (cell == IN_THE_LOOP) == (num == -1)
            out_range_num_c.append(cnstrnt)
            cnstrnt = (cell == OUT_OF_THE_LOOP) == (num >= 0)
            out_range_num_c.append(cnstrnt)

    # the extended/virtual border cells are all 'outside the loop'
    outermost = out_num_board[0] + out_num_board[-1] + list(transpose(out_num_board)[0]) + list(transpose(out_num_board)[-1])
    for num_row in outermost:
        cnstrnt = (num_row >= 0)
        out_range_num_c.append(cnstrnt)

    out_nums = flatten(out_num_board)
    out_single_start_c = [ Exactly(*[n == 0 for n in out_nums], 1) ]

    out_num_at_ = lambda l, c: out_num_board[l][c]
    def gen_out_predecessor_constraints(l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height+2, width=width+2)]
        # the current cell
        cell = out_num_at_(l,c)
        val_neigh_cells = [out_num_at_(*cell) for cell in val_neighs]
        one_neigh_is_predecessor = AtLeast(*[And(neigh_cell >= 0, neigh_cell == cell - 1) for neigh_cell in val_neigh_cells], 1)
        cnstrnt = (cell > 0) == one_neigh_is_predecessor
        return cnstrnt

    out_predecessor_c = [ gen_out_predecessor_constraints(l, c)
        for l, c in itertools.product(range(height+2), range(width+2)) ]

    out_connectivity_c = out_range_num_c + out_single_start_c + out_predecessor_c

    s = Solver()

    s.add( range_walls_c  + count_walls_c + range_loop_c + permeation_c + degree_c + connectivity_c + out_connectivity_c)

    s.check()
    m = s.model()

    return [ [m[cell] for cell in row] for row in walls_board ]

if __name__ == "__main__":
    pars = {'height': 12,
        'puzzle': [[2, 2, 3, 3, -1, 3, -1, 3, -1, -1, -1, 3, 2, -1, -1, -1, 3, 2, -1, 3],
            [-1, 1, 1, -1, 3, -1, 2, -1, -1, -1, 2, -1, 0, -1, -1, -1, 1, -1, 3, -1],
            [-1, -1, -1, 1, 1, 1, -1, -1, 2, -1, 3, -1, 1, -1, 2, -1, -1, -1, -1, 3],
            [2, -1, -1, -1, -1, -1, -1, 3, -1, -1, 1, -1, -1, -1, 2, -1, 3, -1, -1, 3],
            [3, 3, 3, -1, 2, -1, 1, 2, -1, -1, 1, -1, -1, 2, 2, -1, -1, -1, 1, -1],
            [-1, -1, 1, -1, 1, -1, 2, -1, -1, 3, -1, 3, 1, 3, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, 3, 2, -1, -1, -1, -1, 3, -1, -1, 3, -1, -1, 3, -1, 2, -1, 1],
            [-1, -1, 3, -1, -1, -1, 1, 2, -1, -1, 2, 1, -1, -1, -1, -1, -1, 2, -1, 3],
            [3, 1, 1, 2, -1, -1, -1, -1, 3, 2, -1, 2, -1, 3, 1, 0, 3, 1, 2, -1],
            [2, -1, 2, -1, -1, -1, -1, -1, -1, 1, -1, -1, 2, 1, -1, 2, -1, -1, -1, 3],
            [2, -1, 0, -1, 1, 1, -1, 1, 2, 1, -1, 2, -1, -1, -1, 0, -1, -1, -1, 2],
            [2, -1, 1, 1, 1, -1, -1, 2, -1, 3, 2, -1, -1, -1, 3, -1, 3, -1, -1, -1]],
        'width': 20}
    sol = solve_puzzle_slitherlink(**pars)

    hgt = pars['height']

    hws = []
    for walls in sol[:hgt]:
        hws.append(  ' '.join(['|' if w.as_long() == WALL else ' ' for w in walls]))
    vws = []
    for walls in sol[hgt:]:
        vws.append(' ' + (  ' '.join(['—' if w.as_long() == WALL else ' ' for w in walls])))

    for line in itertools.chain(*itertools.zip_longest(vws, hws)):
        print(line)
