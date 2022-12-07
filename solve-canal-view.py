import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 1, 0

# sort of subset_sum
def distribute_in_4_directions(total):
    for i in range(total+1):
        for j in range(total-i+1):
            for k in range(total-i-j+1):
                for l in range(total-i-j-k+1):
                    if i + j + k + l == total:
                        yield(i, j, k, l)

# direction = up, down, left, right, -1, +1, -1, +1

# can also be thought of as 'circle' for a distance
# how much it spawns in each direction
def boundaries(index_, *, spawn_direction):
    up, down, left, right = spawn_direction
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]

# can also be thought of as 'disc' for a distance. without center = without the index_ (current index given as argument).
def get_enclosed_space_wo_center(index_, *, spawn_direction):
    up, down, left, right = spawn_direction
    l, c = index_
    v_spc = [(l+vertic, c) for vertic in range(-up, down+1)
            if vertic != 0]
    h_spc = [(l, c+horiz) for horiz in range(-left, right+1)
            if horiz != 0]
    # we add these conditions to remove index_
    return v_spc + h_spc

# count_ contiguous squares at index_ (l, c)
def gen_contiguous_constraints_single(index_, count_, *, width, height, board):
    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    # count_ (and not count_ - 1) because the current square is discarded
    possibs = [] #possible configurations given the count_ of visible black squares
    for distrib in distribute_in_4_directions(count_):
        strict_boundaries = boundaries(index_, spawn_direction=distrib)
        geom = {'width': width, 'height': height}
        can_spawn = all((inside_board(ind, **geom) for ind in strict_boundaries))
        if can_spawn:
            enclosure = get_enclosed_space_wo_center(index_, spawn_direction = distrib)
            enclosure_vars = get_vars_at(enclosure)
            direction_plus_one = tuple(d + 1 for d in distrib)
            # walls can be thought of as surrounding boundaries
            walls = boundaries(index_,
                    spawn_direction=direction_plus_one)
            walls_within_board = [ind for ind in walls
                    if inside_board(ind, **geom)]
            walls_var = get_vars_at(walls_within_board)
            walled_enclosure = And(
                    coerce_eq(enclosure_vars, [BLACK] * len(enclosure_vars)),
                    coerce_eq(walls_var, [WHITE] * len(walls_var)))
            possibs.append(simplify(walled_enclosure))
    return Exactly(*possibs, 1) #only one configuration would prevail

def gen_contiguous_constraints(puzzle, board, *, width, height):
    pars = {'board': board, 'width': width, 'height': height}
    all_contig_spaces = [ ((i, j), puzzle[i][j])
        for i, j in itertools.product(range(height), range(width))
        if puzzle[i][j] > 0 ]
    constraints = [ gen_contiguous_constraints_single(ind, count_, **pars)
            for ind, count_ in all_contig_spaces ]
    return constraints

def solve_puzzle_canal_view(puzzle, *, height, width):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    pars = {'board': board, 'width': width, 'height': height}

    contig_c = gen_contiguous_constraints(puzzle, **pars)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    instance_c = [ at_(l, c) != BLACK
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]

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

    # CONNECTIVITY of black cells

    range_num_c = []
    # We assign number to each cell in the loop.
    num_board = IntMatrix('num', nb_rows=height, nb_cols=width)
    for row, num_row in zip(board, num_board):
        for cell, num in zip(row, num_row):
            cnstrnt = (cell == WHITE) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (cell == BLACK) == (num >= 0)
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

    s.add( range_c + instance_c + contig_c + density_c + connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Canal-View/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 8,
            'puzzle': #What if 0 is provided as clue? It would be an empty row and an empty column... Then the black cells cannot be contiguous unless the clue is provided at the borders. Then it's merely a puzzle of order-1. So clue given as zero is a degenerate case. We can use 0 to code empty cells.
            ( (0,0,0,0,0,0,6,0),
                (0,0,0,6,0,0,0,0),
                (0,1,5,0,0,0,5,1),
                (0,2,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0),
                (0,3,1,0,0,2,3,2),
                (8,0,0,0,0,0,0,0),
                (0,0,0,1,0,0,2,0) ),
            'width': 8}
    solve_puzzle_canal_view(**pars)
