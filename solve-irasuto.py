import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, inside_board

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
def gen_contiguous_constraints_single(index_, count_, *, width, height, board, color, puzzle):
    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    # count_ (and not count_ - 1) because the current square is discarded
    possibs = [] #possible configurations given the count_ of visible squares of given color
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
            wall_vars = get_vars_at(walls_within_board)
            if len(enclosure_vars) > 1:
                encl_c = coerce_eq(enclosure_vars, [color] * len(enclosure_vars))
            else:
                 encl_c = True
            is_numbered = lambda l, c: puzzle[l][c] >= 0
            wall_c = And(*[ Or(var != color, is_numbered(*idx))
                for var, idx in zip(wall_vars, walls_within_board) ])

            walled_enclosure = And( encl_c, wall_c )
            possibs.append(simplify(walled_enclosure))
    return Exactly(*possibs, 1) #only one configuration would prevail

def gen_contiguous_constraints(puzzle, board, *, width, height, colors):
    pars = {'board': board, 'width': width, 'height': height}

    all_contig_spaces = [ ((i, j), puzzle[i][j], colors[i][j])
        for i, j in itertools.product(range(height), range(width))
        if puzzle[i][j] >= 0 and colors[i][j] in 'bw' ]
    color_map = { 'b': BLACK, 'w': WHITE }
    constraints = [ gen_contiguous_constraints_single(ind, count_, **pars, color=color_map[clr], puzzle=puzzle)
            for ind, count_, clr in all_contig_spaces ]
    return constraints


def solve_puzzle_irasuto(puzzle, *, height, width, colors):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    color_map = { 'b': BLACK, 'w': WHITE }
    instance_c = [ at_(l, c) == color_map[colors[l][c]]
            for l, c in itertools.product(range(height), range(width))
            if colors[l][c] in 'bw' ]


    pars = {'board': board, 'width': width, 'height': height}
    contig_c = gen_contiguous_constraints(puzzle, **pars, colors=colors)

    s = Solver()

    s.add( range_c + instance_c + contig_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Irasuto/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'puzzle':
            (  (2,-1,0,0,1,-1,2,1,-1,1),
                (-1,3,-1,-1,-1,2,-1,-1,2,-1),
                (1,0,0,0,-1,2,1,2,1,-1),
                (2,-1,-1,2,1,-1,2,-1,0,1),
                (0,-1,1,-1,1,-1,3,-1,2,0),
                (-1,2,2,-1,2,1,-1,1,-1,1),
                (-1,1,-1,0,-1,2,-1,1,-1,1),
                (1,-1,1,1,1,-1,2,0,2,-1),
                (-1,2,-1,-1,2,-1,-1,1,-1,0),
                (1,-1,2,1,-1,1,1,0,1,0)),
            'colors':
            (tuple('b wbw ww b'),
             tuple(' b   w  b '),
             tuple('bwwb bwbw '),
             tuple('b  ww b ww'),
             tuple('b b w w bb'),
             tuple(' ww ww b b'),
             tuple(' b b w b b'),
             tuple('b bww wbw '),
             tuple(' w  w  b b'),
             tuple('b bw bbbww')),

            'width': 10}
    solve_puzzle_irasuto(**pars)
