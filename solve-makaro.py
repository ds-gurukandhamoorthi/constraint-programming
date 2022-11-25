import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, get_same_block_indices, rows_and_cols, inside_board
from more_itertools import pairwise

EMPTY = 0

def solve_puzzle_makaro(puzzle, *, height, width, cage_ids, orthogonal_max):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    # empty cells or cells with clues
    black_cells = cages_inds[0]

    empty_c = [ And([ cell == EMPTY for cell in get_vars_at(black_cells)]) ]

    # remove empty cells from constraints on cages
    del cages_inds[0]

    max_cage_size = 0
    cage_range_c = []
    cage_elems_distinct_c = []
    for board_indices in cages_inds.values():
        vars_ = get_vars_at(board_indices)
        cage_size = len(vars_)
        max_cage_size = max(cage_size, max_cage_size)
        cnstrnts = [ And(var >= 1, var <= cage_size) for var in vars_ ]
        cage_range_c.extend(cnstrnts)
        cage_elems_distinct_c.append(Distinct(vars_))

    adj_c = []
    for line in rows_and_cols(board):
        for cell_1, cell_2 in pairwise(line):
            # If two adjacent cells not empty ( contains a number >= 1) then those two numbers must be different
            not_empty = And(cell_1 > 0, cell_2 > 0)
            cnstrnt = Implies(not_empty, cell_1 != cell_2)
            adj_c.append( cnstrnt )

    def get_ortho_neigh(l, c, direc):
        up, down, left, right = (1, 1, 1, 1)
        if direc == 'v':
            return (l+down, c)
        if direc == '^':
            return (l-up, c)
        if direc == '<':
            return (l, c-left)
        if direc == '>':
            return (l, c+right)

    ortho_neigh_max_c = []
    for l, c, direc in orthogonal_max:
        other_neighs = [get_ortho_neigh(l, c, d) for d in '^v<>' if d != direc ]
        val_neighs = [ neigh for neigh in other_neighs
                if inside_board(neigh, height=height, width=width)]
        max_neigh = get_ortho_neigh(l, c, direc)
        # cell pointed by the arrow in the clue which contains max
        max_neigh_cell = at_(*max_neigh)
        # valid neighbour cells
        val_neigh_cells = [at_(*cell) for cell in val_neighs]
        cnstrnt = And([ max_neigh_cell > cell for cell in val_neigh_cells ])
        ortho_neigh_max_c.append(cnstrnt)

    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0 ]


    s = Solver()

    s.add( empty_c + cage_range_c + cage_elems_distinct_c + adj_c + ortho_neigh_max_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Makaro/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'puzzle':
            ( (0,0,0,0,4,0,0,2,0,0),
                (4,0,0,0,0,1,0,0,0,4),
                (0,0,2,0,4,0,1,0,0,1),
                (0,0,0,0,0,0,0,3,2,0),
                (0,0,0,0,1,0,4,0,4,0),
                (0,0,0,2,4,5,1,4,0,2),
                (0,0,2,0,0,0,0,0,0,1),
                (3,0,0,0,4,2,0,3,0,0),
                (0,0,3,0,0,0,3,0,3,0),
                (2,0,0,2,0,4,0,1,0,3)),
            'cage_ids':
            ( (0,1,2,2,2,3,3,4,4,0),
                (1,1,0,2,0,5,0,6,6,7),
                (0,1,8,0,5,5,9,0,7,7),
                (8,8,8,8,5,0,9,10,7,11),
                (0,0,12,0,12,13,13,10,11,11),
                (14,14,12,12,12,13,13,10,10,11),
                (0,14,15,0,16,13,17,17,18,18),
                (19,0,15,16,16,16,0,17,0,20),
                (19,21,21,22,0,23,23,0,20,20),
                (19,0,21,22,22,23,23,24,24,24)),
            'orthogonal_max': [(0, 0, 'v'), (0, 9, 'v'), (1, 2, '<'), (2, 3, 'v'), (3, 5, '^'), (4, 0, '^'), (4, 1, '>'), (6, 3, 'v'), (7, 1, '<'), (8, 4, '^')],
            'width': 10}
    solve_puzzle_makaro(**pars)
