import itertools
from z3 import *
from more_z3 import IntMatrix, BoolMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board, rows_and_cols, transpose
from more_itertools import pairwise, windowed
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 0, 1
# We use id=0 (BLACK) id of block > 0 (WHITE)

def solve_puzzle_nuribou(puzzle, *, height, width):

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
    for line in rows_and_cols(block_id_board):
        for cell_l, cell_r in pairwise(line):
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

    # To describe that black stripes must have a width of 1, we can say any square in the grid can have at most 2 black squares. A black strip of width greater than 1 would have more than 2 black squares in one of the squares.
    black_stripe_c = []

    at_ = lambda l, c : block_id_board[l][c]
    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        black_cells_in_a_square = [ at_(*cell) == BLACK for cell in val_cells_in_square ]
        # The following constraint would in a context-free manner force black lines to have a length of 1 (stripes).
        return AtMost(*black_cells_in_a_square, 2)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    black_stripe_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    def is_black_stripe(lst):
        white_cells_at_extremities = And(lst[0] != BLACK, lst[-1] != BLACK)
        black_strip_in_between = And([cell == BLACK for cell in lst[1:-1]])
        return And(white_cells_at_extremities, black_strip_in_between)

    adj_black_stripes_c = []

    # pad with that many number of white cells on each extremity
    pad_white_cells = lambda x, n=1: [WHITE] * n  + list(x) + [WHITE] * n

    for row, nxt_row in pairwise(block_id_board):
        # If strip length greater than half width/height... the next row/col couldn't be a strip of same size
        for strp_len in range(2, math.ceil(width/2) + 1):
            windows = windowed(pad_white_cells(row), strp_len+2)
            # each black strip (window) constrains two windows of the next row/col to have a different length (we call it nxt_wnd, nxt_offset_window)
            #windows in next row/col
            nxt_windows = list(windowed(pad_white_cells(nxt_row, n=strp_len+1), strp_len+2))
            offset = 1 + 2*strp_len - 1
            nxt_offset_windows = nxt_windows[offset:]
            for wnd, nxt_wnd, nxt_ofst_wnd in zip(windows, nxt_windows, nxt_offset_windows):
                black_strip_of_given_length = is_black_stripe(wnd)
                nxt_wnd_black_strip_of_same_length = is_black_stripe(nxt_wnd)
                nxt_ofst_wnd_black_strip_of_same_length = is_black_stripe(nxt_ofst_wnd)
                cnstrnt = Implies(black_strip_of_given_length, Not(nxt_wnd_black_strip_of_same_length))
                adj_black_stripes_c.append(cnstrnt)
                cnstrnt = Implies(black_strip_of_given_length, Not(nxt_ofst_wnd_black_strip_of_same_length))
                adj_black_stripes_c.append(cnstrnt)

    for col, nxt_col in pairwise(transpose(block_id_board)):
        # If strip length greater than half width/height... the next col/col couldn't be a strip of same size
        for strp_len in range(2, math.ceil(height/2) + 1):
            windows = windowed(pad_white_cells(col), strp_len+2)
            # each black strip (window) constrains two windows of the next col/col to have a different length (we call it nxt_wnd, nxt_offset_window)
            #windows in next col/col
            nxt_windows = list(windowed(pad_white_cells(nxt_col, n=strp_len+1), strp_len+2))
            offset = 1 + 2*strp_len - 1
            nxt_offset_windows = nxt_windows[offset:]
            for wnd, nxt_wnd, nxt_ofst_wnd in zip(windows, nxt_windows, nxt_offset_windows):
                black_strip_of_given_length = is_black_stripe(wnd)
                nxt_wnd_black_strip_of_same_length = is_black_stripe(nxt_wnd)
                nxt_ofst_wnd_black_strip_of_same_length = is_black_stripe(nxt_ofst_wnd)
                cnstrnt = Implies(black_strip_of_given_length, Not(nxt_wnd_black_strip_of_same_length))
                adj_black_stripes_c.append(cnstrnt)
                cnstrnt = Implies(black_strip_of_given_length, Not(nxt_ofst_wnd_black_strip_of_same_length))
                adj_black_stripes_c.append(cnstrnt)

    # These are special/degenerate cases. Width of 1 means they can be horizontal or vertical. And by merely reading rows or cols one can't say if it's of width 1
    single_black_cells = BoolMatrix('sngl_b', nb_rows=height, nb_cols=width)

    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    for l, c in itertools.product(range(height), range(width)):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width) ]
        neighs = get_vars_at(val_neighs)
        var = at_(l, c) #content of current cell
        delimited_by_white = And([cell != BLACK for cell in neighs])
        single_black_cells[l][c] = And( var == BLACK, delimited_by_white )

    single_at_ = lambda l, c : single_black_cells[l][c]
    def gen_single_black_cell_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        single_black_cells_in_square = [ single_at_(*cell) == True for cell in val_cells_in_square ]
        # The following constraint would disallow a black strip of width 1 adjacent to another one.
        return AtMost(*single_black_cells_in_square, 1)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    single_black_stripe_adj_c = [ gen_single_black_cell_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    s = Solver()

    s.add( block_id_range_c + block_id_instance_c + block_size_c + connectivity_c + adj_c + size_c + black_stripe_c + adj_black_stripes_c + single_black_stripe_adj_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in block_id_board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Nuribou/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'puzzle':
            ( (0,0,0,0,0,0,6,0),
               (0,0,0,0,0,0,0,0),
               (0,0,0,0,0,0,0,0),
               (0,0,7,0,0,0,0,0),
               (1,0,0,0,0,0,0,9),
               (0,2,0,0,0,0,0,0),
               (0,0,0,0,0,6,0,0),
               (1,0,1,0,0,0,0,0),
                ),
            'width': 8}
    solve_puzzle_nuribou(**pars)
