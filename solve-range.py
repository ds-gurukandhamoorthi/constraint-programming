import itertools
from z3 import *

#transpose a matrix
transpose = lambda m: list(zip(*m))

BLACK, WHITE = 0, 1

def flatten(list_of_lists):
    return list(itertools.chain(*list_of_lists))

def IntMatrix(prefix, nb_rows, nb_cols):
    res = [[ Int(f'{prefix}_{i}_{j}') for j in range(nb_cols)]
                            for i in range(nb_rows) ]
    return res

def coerce_eq(variabs, vals):
    variabs = list(variabs)
    vals = list(vals)
    assert len(variabs) == len(vals), 'Lengths of the variables and values must be equal for the intended coercing between them'
    return And([ var == v for var, v in zip(variabs, vals) ])


# sort of subset_sum
def distribute_in_4_directions(total):
    for i in range(total+1):
        for j in range(total-i+1):
            for k in range(total-i-j+1):
                for l in range(total-i-j-k+1):
                    if i + j + k + l == total:
                        yield(i, j, k, l)

# direction = up, down, left, right, -1, +1, -1, +1

# index = line, column
def inside_board(index_lc, *, height, width):
    l, c = index_lc
    return (0 <= l < height) and (0 <= c < width)

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
                    coerce_eq(encloure_vars, [WHITE] * len(encloure_vars)),
                    coerce_eq(walls_var, [BLACK] * len(walls_var)))
            possibs.append(simplify(walled_enclosure))
    return PbEq([(p, 1) for p in possibs], 1) #only one configuration would prevail

def gen_contiguous_constraints(puzzle, board, *, width, height):
    pars = {'board': board, 'width': width, 'height': height}
    all_contig_spaces = [ ((i, j), puzzle[i][j])
        for i, j in itertools.product(range(height), range(width))
        if puzzle[i][j] > 0 ]
    constraints = [ gen_contiguous_constraints_single(ind, count_, **pars)
            for ind, count_ in all_contig_spaces ]
    return constraints

def solve_puzzle_range(puzzle, *, height, width):
    board = IntMatrix('b', nb_rows=height, nb_cols=width)
    pars = {'board': board, 'width': width, 'height': height}

    contig_c = gen_contiguous_constraints(puzzle, **pars)

    # There is no empty cell:
    complete_c = [ Xor(cell == WHITE, cell == BLACK)
            for cell in flatten(board) ]

    # No two black squares are adjacent: horizontal
    horiz_bl_c = [ [And(cell_1 == BLACK, cell_2 == BLACK)
            for cell_1, cell_2 in zip(row, row[1:]) ]
            for row in board ]
    horiz_bl_c = flatten(horiz_bl_c)

    horiz_bl_c = AtMost(*horiz_bl_c, 0)

    # No two black squares are adjacent: vertical
    vertic_bl_c = [ [And(cell_1 == BLACK, cell_2 == BLACK)
            for cell_1, cell_2 in zip(row, row[1:]) ]
            for row in transpose(board) ]
    vertic_bl_c = flatten(vertic_bl_c)

    vertic_bl_c = AtMost(*vertic_bl_c, 0)

    # No two black squares are adjancent: vertically or horizontall (ortho)
    ortho_bl_c = [ horiz_bl_c, vertic_bl_c ]


    s = Solver()

    s.add(contig_c + complete_c + ortho_bl_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    puzzle_h6_w9 = [
            [0, 0, 8, 0, 0, 0, 12, 0, 7],
            [4, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 5, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 6],
            [4, 0, 4, 0, 0, 0, 9, 0, 0]]

    width, height= 9, 6 # a.k.a nb_columns, nb_rows

    solve_puzzle_range(puzzle_h6_w9, height=height, width=width)

    puzzle_h11_w16 = [
            [0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0],
            [0, 0, 0, 0, 4, 0, 12, 12, 0, 17, 0, 0, 0, 13, 0, 14],
            [0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 6, 0, 5],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 8, 0, 0, 7, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0],
            [0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0],
            [0, 0, 0, 17, 0, 0, 0, 14, 0, 0, 14, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [11, 0, 7, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0],
            [9, 0, 5, 0, 0, 0, 9, 0, 6, 3, 0, 6, 0, 0, 0, 0],
            [0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0]]

    width, height= 16, 11 # a.k.a nb_columns, nb_rows
    sol = solve_puzzle_range(puzzle_h11_w16, height=height, width=width)
