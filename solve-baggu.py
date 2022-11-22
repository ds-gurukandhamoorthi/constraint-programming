import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board, transpose
from more_itertools import pairwise
from collections import defaultdict
from puzzles_common import ortho_neighbours as neighbours

WALL, POROUS = 1, 0
IN_THE_LOOP, OUT_OF_THE_LOOP = 1, 0

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

# can also be thought of as 'disc' for a distance
def get_enclosed_space(index_, *, spawn_direction):
    up, down, left, right = spawn_direction
    l, c = index_
    v_spc = [(l+vertic, c) for vertic in range(-up, down+1)]
    h_spc = [(l, c+horiz) for horiz in range(-left, right+1)
            if c + horiz != c]
    return v_spc + h_spc
    # we add this condition to avoid repetition of the square at index_


# count_ contiguous squares at index_ (l, c)
def gen_contiguous_constraints_single(index_, count_, *, width, height, board):
    at_ = lambda l, c : board[l][c]
    # count_ - 1 because the current square is always counted
    possibs = [] #possible configurations given the count_ of white squares
    for distrib in distribute_in_4_directions(count_ - 1):
        strict_boundaries = boundaries(index_, spawn_direction=distrib)
        geom = {'width': width, 'height': height}
        can_spawn = all((inside_board(ind, **geom) for ind in strict_boundaries))
        if can_spawn:
            enclosure = get_enclosed_space(index_, spawn_direction = distrib)
            encloure_vars = [ at_(*ind) for ind in enclosure ]
            direction_plus_one = tuple(d + 1 for d in distrib)
            # walls can be thought of as surrounding boundaries
            walls = boundaries(index_,
                    spawn_direction=direction_plus_one)
            walls_within_board = [ind for ind in walls
                    if inside_board(ind, **geom)]
            walls_var = [at_(*ind) for ind in walls_within_board]
            walled_enclosure = And(
                    coerce_eq(encloure_vars, [IN_THE_LOOP] * len(encloure_vars)),
                    coerce_eq(walls_var, [OUT_OF_THE_LOOP] * len(walls_var)))
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

def solve_puzzle_baggu(puzzle, *, height, width):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == IN_THE_LOOP, cell == OUT_OF_THE_LOOP)
            for cell in flatten(board) ]

    # This may be redundant
    numbered_cells_inside_loop_c = []
    for row, puzzle_row in zip(board, puzzle):
        for cell, num in zip(row, puzzle_row):
            if num > 0:
                cnstrnt = cell == IN_THE_LOOP
                numbered_cells_inside_loop_c.append(cnstrnt)

    pars = {'board': board, 'width': width, 'height': height}
    # This is noted as contiguous constraint. Here it's more like contiguous squares that are visible from the current square. We shall keep the name so that we know we've copy-pasted from solve-range.py
    contig_c = gen_contiguous_constraints(puzzle, **pars)

    #WALLS

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

    permeation_c = []
    for row, walls in zip(board, lr_walls_board):
        # walls[1:-1] we skip the walls at the extremities of the playing-field
        for adj_cells, wall in zip(pairwise(row), walls[1:-1]):
            cnstrnt = Implies(wall == POROUS, adj_cells[0] == adj_cells[1])
            permeation_c.append(cnstrnt)
            cnstrnt = Implies(wall == WALL, adj_cells[0] != adj_cells[1])
            permeation_c.append(cnstrnt)
    for col, walls in zip(transpose(board), transpose(tb_walls_board)):
        for adj_cells, wall in zip(pairwise(col), walls[1:-1]):
            cnstrnt = Implies(wall == POROUS, adj_cells[0] == adj_cells[1])
            permeation_c.append(cnstrnt)
            cnstrnt = Implies(wall == WALL, adj_cells[0] != adj_cells[1])
            permeation_c.append(cnstrnt)

    #Note: having previous walls_at dictionary and the following function with the same name is unfortunate.
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

    # no "porous" wall on the loop at the border of the board
    # Note: this is not sufficient to avoid islands inside
    isolation_c = []
    for i in (0, -1):
        for wall, cell in zip(tb_walls_board[i], board[i]):
            cnstrnt = (wall == POROUS) == (cell == OUT_OF_THE_LOOP)
            isolation_c.append(cnstrnt)
        for wall, cell in zip(transpose(lr_walls_board)[i], transpose(board)[i]):
            cnstrnt = (wall == POROUS) == (cell == OUT_OF_THE_LOOP)
            isolation_c.append(cnstrnt)

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

    s.add( range_c + numbered_cells_inside_loop_c + contig_c + range_walls_c + permeation_c + degree_c + connectivity_c + isolation_c + out_connectivity_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in walls_board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Corral/007.a.htm by author Mokuani (https://mokuani.hatenablog.com/)
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    # there's no need for using -1 for number of cells visible. as the current cell is counted on... normally numbers >= 2. So encoding empty cells as 0 is ok.
    pars = {'height': 10,
            'puzzle':
            (   (2,0,0,2,0,0,0,4,0,0),
                (0,0,0,0,0,0,6,0,5,0),
                (4,0,0,3,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,2,0,0),
                (0,0,2,0,7,0,0,0,0,0),
                (0,0,0,0,0,4,0,6,0,0),
                (0,0,5,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,4,0,0,10),
                (0,2,0,3,0,0,0,0,0,0),
                (0,0,10,0,0,0,12,0,0,19)),
            'width': 10}
    sol = solve_puzzle_baggu(**pars)

    hgt = pars['height']

    hws = []
    for walls in sol[:hgt]:
        hws.append(  ' '.join(['|' if w.as_long() == WALL else ' ' for w in walls]))
    vws = []
    for walls in sol[hgt:]:
        vws.append(' ' + (  ' '.join(['—' if w.as_long() == WALL else ' ' for w in walls])))

    for line in itertools.chain(*itertools.zip_longest(vws, hws)):
        print(line)
