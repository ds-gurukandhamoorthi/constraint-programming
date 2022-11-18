import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board, transpose
from more_itertools import pairwise

BLACK, WHITE = 0, 1
# We use id=0 (BLACK) id of block > 0 (WHITE)

def neighbours(index_):
    up, down, left, right = (1, 1, 1, 1)
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]


def solve_puzzle_nurikabe(puzzle, *, height, width):

    def get_id(l, c):
        return (l * width + c + 1)

    # We give id to contiguous white cells... which block they belong to. id = 0 (black cell)
    block_id_board = IntMatrix('b_i', nb_rows=height, nb_cols=width)

    block_id_range_c = [ And(bl_id >= 0, bl_id <= height * width)
            for bl_id in flatten(block_id_board) ]

    block_id_instance_c = [ block_id_board[l][c] == get_id(l, c)
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0
            ]

    block_id_and_count = []
    for l, c in itertools.product(range(height), range(width)):
        block_count = puzzle[l][c]
        if block_count > 0:
            block_id_and_count.append((get_id(l,c), block_count))

    nb_white_regions = len(block_id_and_count)

    # CONNECTIVITY of cells with given id

    range_num_c = []
    num_boards = [ IntMatrix(f'n_for{i}', nb_rows=height, nb_cols=width)
            for i in range(nb_white_regions) ]

    for i in range(nb_white_regions):
        for block_ids_row, num_row in zip(block_id_board, num_boards[i]):
            for block_id, num in zip(block_ids_row, num_row):
                given_block_id = block_id_and_count[i][0]
                cnstrnt = (block_id != given_block_id) == (num == -1)
                range_num_c.append(cnstrnt)
                cnstrnt = (block_id == given_block_id) == (num >= 0)
                range_num_c.append(cnstrnt)

    single_start_c = []
    for i in range(nb_white_regions):
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
        for n, l, c in itertools.product(range(nb_white_regions), range(height), range(width)) ]

    # connectivity constraint as proposed by Gerhard van der Knijff in 'Solving and generating puzzles with a connectivity constraint'
    # This can be thought of as a creative use of proof-by-induction and Peano's way of definining natural numbers...
    # Some seed/start ... then everything spawns from it.
    connectivity_c = range_num_c + single_start_c + predecessor_c

    block_size_c = []
    for i, (_bl_id, bl_sz) in enumerate(block_id_and_count):
        cnstrnt = Sum([n >= 0 for n in flatten(num_boards[i])]) == bl_sz
        block_size_c.append(cnstrnt)

    # Two white cells belonging to different blocks are not adjacent.
    adj_c = []
    for row in block_id_board:
        for cell_l, cell_r in pairwise(row):
            both_white_cells = And(cell_l > 0, cell_r > 0)
            cnstrnt = Implies(both_white_cells, cell_l == cell_r)
            adj_c.append(cnstrnt)
    for col in transpose(block_id_board):
        for cell_l, cell_r in pairwise(col):
            both_white_cells = And(cell_l > 0, cell_r > 0)
            cnstrnt = Implies(both_white_cells, cell_l == cell_r)
            adj_c.append(cnstrnt)

    size_c = []

    nb_white_cells = sum([cnt for _, cnt in block_id_and_count])
    nb_black_cells = height * width - nb_white_cells

    for i, (bl_id, bl_sz) in enumerate(block_id_and_count):
        cnstrnt = Sum([n == bl_id for n in flatten(block_id_board)]) == bl_sz
        size_c.append(cnstrnt)

    cnstrnt = Sum([n == BLACK for n in flatten(block_id_board)]) == nb_black_cells
    size_c.append(cnstrnt)

    # Note: instead of separate connnectivity logic for black cells one can also append to block_id_board [(0, nb_black_cells)] with id=0 meaning black cell...

    # CONNECTIVITY of black cells

    black_range_num_c = []
    # We assign number to each black cell
    black_num_board = IntMatrix('black_n', nb_rows=height, nb_cols=width)
    for row, num_row in zip(block_id_board, black_num_board):
        for bl_id, num in zip(row, num_row):
            # block ids greater than 0 are white cells
            cnstrnt = (bl_id > 0) == (num == -1)
            black_range_num_c.append(cnstrnt)
            cnstrnt = (bl_id == 0) == (num >= 0)
            black_range_num_c.append(cnstrnt)

    black_nums = flatten(black_num_board)
    black_single_start_c = [ Exactly(*[n == 0 for n in black_nums], 1) ]


    black_num_at_ = lambda l, c: black_num_board[l][c]
    def gen_predecessor_constraints_black(l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        # the current cell
        cell = black_num_at_(l,c)
        val_neigh_cells = [black_num_at_(*cell) for cell in val_neighs]
        one_neigh_is_predecessor = AtLeast(*[And(neigh_cell >= 0, neigh_cell == cell - 1) for neigh_cell in val_neigh_cells], 1)
        cnstrnt = (cell > 0) == one_neigh_is_predecessor
        return cnstrnt


    black_predecessor_c = [ gen_predecessor_constraints_black(l, c)
        for l, c in itertools.product(range(height), range(width)) ]

    black_connectivity_c = black_range_num_c + black_single_start_c + black_predecessor_c

    at_ = lambda l, c: block_id_board[l][c]

    # similar to gen_proximity_constraints in solve-tents.py
    # A square of 4 black cells or larger is forbidden.
    def gen_density_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        black_cells_in_the_square = [ at_(*cell) == BLACK for cell in val_cells_in_square ]
        return AtMost(*black_cells_in_the_square, 3)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    density_c = [ gen_density_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    s = Solver()

    s.add( block_id_range_c + block_id_instance_c + connectivity_c + block_size_c + connectivity_c + adj_c + size_c + black_connectivity_c + density_c )

    s.check()
    m = s.model()

    return [ [m[cell] for cell in row] for row in block_id_board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Nurikabe/0007.a.htm by author Warai Kamosika (https://mokuani.hatenablog.com/)
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'puzzle':
                ((4,0,1,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,7,0,0,2),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,0,0,2,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,0),
                (10,0,0,0,1,0,3,0,0,5),
                (0,0,0,0,0,3,0,0,4,0),
                (0,0,0,0,0,0,0,0,0,0),
                (0,0,2,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,7)
                ),
            'width': 10}
    solve_puzzle_nurikabe(**pars)
