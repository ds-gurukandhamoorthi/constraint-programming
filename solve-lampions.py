import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board

BLACK, WHITE = 0, 1

# neighbour (adjacent) cells including the cell itself
def neighbours(index_):
    l, c = index_
    for i, j in itertools.product([-1, 0, 1], repeat=2):
        yield(l + i, c + j)

def solve_puzzle_lampions(*, height, width, clues):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    exist_one_white_c = [ Or([ cell == WHITE
    for cell in flatten(board) ]) ]

    at_ = lambda l, c : board[l][c]

    color_dependent_count_c = []

    for l, c in itertools.product(range(height), range(width)):
        clue = clues[l][c]
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        val_neigh_cells = [at_(*cell) for cell in val_neighs]
        val_neigh_white_cells = [ cell == WHITE for cell in val_neigh_cells ]
        clue_is_count_of_neighbours = Exactly(*val_neigh_white_cells, clue)
        curr_cell_is_white = board[l][c] == WHITE
        # This equivalence (double-implication) along with the fact that cells are Either White or Black
        # permits to not add if current cell is black count-of-neighbour-white-cells is different from clue
        cnstrnt = curr_cell_is_white == clue_is_count_of_neighbours
        color_dependent_count_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + exist_one_white_c + color_dependent_count_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Lampions/217.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 5,
            #clues = color-dependent-count-of-adjacent-neighbours
            'clues': ( (2,4,4,5,4),
                (6,5,6,6,5),
                (3,4,6,3,5),
                (5,2,5,6,4),
                (3,3,4,6,3) ),
            'width': 5}
    solve_puzzle_lampions(**pars)

