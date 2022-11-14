import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board
from collections import defaultdict
from more_itertools import pairwise

WALL, POROUS = 1, 0

def neighbours(index_):
    up, down, left, right = (1, 1, 1, 1)
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]

def solve_puzzle_palisade(puzzle, *, height, width, region_size):
    nb_regions = ( height * width ) // region_size
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

    outermost = flatten([transpose(lr_walls_board)[0], transpose(lr_walls_board)[-1], tb_walls_board[0], tb_walls_board[-1]])
    # The board is closed. Walls on the border. No opening.
    closed_space_c = [w == WALL for w in outermost]

    # We give id to cells... which block they belong to. 0 <= id < nb_regions
    block_id_board = IntMatrix('b_i', nb_rows=height, nb_cols=width)

    block_id_range_c = [ And(bl_id >= 0, bl_id < nb_regions)
            for bl_id in flatten(block_id_board) ]

    block_id_count_c = []
    for i in range(nb_regions):
        nb_blocks_with_given_id = Sum([bl_id == i for bl_id in flatten(block_id_board)])
        cnstrnt = nb_blocks_with_given_id == region_size
        block_id_count_c.append(cnstrnt)

    whole_tally_c = [ Sum(list(flatten(block_id_board))) == sum([region_size * i for i in range(nb_regions)])  ]

    permeation_c = []
    for row, walls in zip(block_id_board, lr_walls_board):
        # walls[1:-1] we skip the walls at the extremities of the playing-field
        for adj_block_ids, wall in zip(pairwise(row), walls[1:-1]):
            cnstrnt = Implies(wall == POROUS, adj_block_ids[0] == adj_block_ids[1])
            permeation_c.append(cnstrnt)
            cnstrnt = Implies(wall == WALL, adj_block_ids[0] != adj_block_ids[1])
            permeation_c.append(cnstrnt)
    for row, walls in zip(transpose(block_id_board), transpose(tb_walls_board)):
        for adj_block_ids, wall in zip(pairwise(row), walls[1:-1]):
            cnstrnt = Implies(wall == POROUS, adj_block_ids[0] == adj_block_ids[1])
            permeation_c.append(cnstrnt)
            cnstrnt = Implies(wall == WALL, adj_block_ids[0] != adj_block_ids[1])
            permeation_c.append(cnstrnt)

    def walls_at(l, c):
        for offset in [-1, 0]:
            if 0 <= l+offset < height:
                yield lr_walls_board[l+offset][c]
            if 0 <= c+offset < width:
                yield tb_walls_board[l][c+offset]

    # constraint on degree as proposed by Gerhard van der Knijff in 'Solving and generating puzzles with a connectivity constraint'
    # On this puzzle this can be seen as avoiding isolated walls
    degree_c = []
    for l in range(height+1):
        for c in range(width+1):
            cnstrnt = Or(Sum(list(walls_at(l, c))) == 4,
                    Sum(list(walls_at(l, c))) == 3,
                    Sum(list(walls_at(l, c))) == 2,
                    Sum(list(walls_at(l, c))) == 0)
            degree_c.append(cnstrnt)

    # CONNECTIVITY of cells with given id

    range_num_c = []
    num_boards = [ IntMatrix(f'n_for{i}', nb_rows=height, nb_cols=width)
            for i in range(nb_regions) ]

    for i in range(nb_regions):
        for block_ids_row, num_row in zip(block_id_board, num_boards[i]):
            for block_id, num in zip(block_ids_row, num_row):
                cnstrnt = (block_id != i) == (num == -1)
                range_num_c.append(cnstrnt)
                cnstrnt = (block_id == i) == (num >= 0)
                range_num_c.append(cnstrnt)

    single_start_c = []
    for i in range(nb_regions):
        nums = flatten(num_boards[i])
        cnstrnt = Exactly(*[n == 0 for n in nums], 1)
        single_start_c.append(cnstrnt)

    num_at_ = lambda n, l, c: num_boards[n][l][c]
    def gen_predecessor_constraints(n, l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        # the current cell
        cell = num_at_(n,l,c)
        val_neigh_cells = [num_at_(n, *cell) for cell in val_neighs]
        one_neigh_is_predecessor = AtLeast(*[And(neigh_cell >= 0, neigh_cell == cell - 1) for neigh_cell in val_neigh_cells], 1)
        cnstrnt = (cell > 0) == one_neigh_is_predecessor
        return cnstrnt


    predecessor_c = [ gen_predecessor_constraints(n, l, c)
        for n, l, c in itertools.product(range(nb_regions), range(height), range(width)) ]

    s = Solver()

    s.add( range_walls_c + count_walls_c + closed_space_c + block_id_range_c + permeation_c + degree_c + range_num_c + single_start_c + predecessor_c + block_id_count_c + whole_tally_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in walls_board ]

if __name__ == "__main__":
    pars = {'height': 6,
            'puzzle': [[-1, -1, -1, -1, -1, -1, 1, -1],
                [-1, -1, 2, 3, 1, -1, 1, -1],
                [-1, -1, 1, 2, -1, -1, 1, -1],
                [-1, 2, 3, -1, -1, -1, -1, 2],
                [1, -1, -1, -1, -1, -1, -1, 2],
                [-1, -1, -1, -1, -1, -1, 1, -1]],
            'region_size': 6,
            'width': 8}
    sol = solve_puzzle_palisade(**pars)

    hgt = pars['height']

    hws = []
    for walls in sol[:hgt]:
        hws.append(  ' '.join(['|' if w.as_long() == WALL else ' ' for w in walls]))
    vws = []
    for walls in sol[hgt:]:
        vws.append(' ' + (  ' '.join(['—' if w.as_long() == WALL else ' ' for w in walls])))

    for line in itertools.chain(*itertools.zip_longest(vws, hws)):
        print(line)
