import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, ortho_neighbours as neighbours, inside_board

EMPTY = 0
# White cells must contain number (filled). Black cells must be empty

# In `puzzle`
TO_BE_FILLED = 0

# excluding the 'current'/given-as-argument cell-index
def orthogonal_strips(index_, *, height, width):
    l, c = index_
    horiz = ((l, c_) for c_ in range(width)
            if c_ != c)
    vert = ((l_, c) for l_ in range(height)
            if l_ != l)
    yield from horiz
    yield from vert

# excluding the 'current'/given-as-argument cell-index
def diagonal_strips(index_, *, height, width):
    l, c = index_
    north_west = ((l - l_off , c - c_off)
            for l_off, c_off in zip(range(l+1), range(c+1))
            if c_off != 0 and l_off != 0)
    south_east = ((l_, c_)
            for l_, c_ in zip(range(l+1, height), range(c+1, width)))
    north_east = ((l - l_off , c_)
            for l_off, c_ in zip(range(l+1), range(c, width))
            if l_off != 0)
    south_west = ((l_, c - c_off)
            for l_, c_off in zip(range(l, height), range(c+1))
            if c_off != 0)
    yield from north_west
    yield from south_east
    yield from north_east
    yield from south_west

def solve_puzzle_zipline(puzzle, *, height, width):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    nb_white_cells = sum(n == TO_BE_FILLED for n in flatten(puzzle))
    max_possible_number = nb_white_cells

    range_c = [ And(cell >= 0, cell <= max_possible_number)
            for cell in flatten(board) ]

    def get_id(l, c):
        return -(l * width + c + 1)

    id_board = [[get_id(l, c) for c in range(width)]
            for l in range(height)]

    distinct_c = Distinct([ var if given == TO_BE_FILLED else id_
        for given, var, id_ in zip(flatten(puzzle), flatten(board), flatten(id_board)) ])
    distinct_c = [ distinct_c ]

    instance_c = []
    for given, var in zip(flatten(puzzle), flatten(board)):
        if given > 0:
            instance_c.append( var == EMPTY)
        else:
            instance_c.append( var > 0 )

    ortho_sum_c = []

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    for l, c in itertools.product(range(height), range(width)):
        sum_ = puzzle[l][c]
        if sum_ > 0:
            val_neighs = [ neigh for neigh in neighbours((l, c))
                    if inside_board(neigh, height=height, width=width) ]
            neighs = get_vars_at(val_neighs)
            cnstrnt = Sum(neighs) == sum_
            ortho_sum_c.append(cnstrnt)

    # Any even number's odd-predecessor is in the row or column
    ortho_strip_c = []
    for n in range(2, max_possible_number + 1, 2):
        for l, c in itertools.product(range(height), range(width)):
            if puzzle[l][c] == TO_BE_FILLED:
                ortho_indxs = list(orthogonal_strips((l,c), height=height, width=width))
                # other cells in the row or column
                other_cells_in_orthogonal_strip = get_vars_at(ortho_indxs)
                strip_contains_predecessor = Or([ cell == n-1
                    for cell in other_cells_in_orthogonal_strip ])
                cnstrnt = Implies(board[l][c] == n, strip_contains_predecessor)
                ortho_strip_c.append(cnstrnt)

    # Any odd number's odd-predecessor is in one of the diagonals containing it.
    diag_strip_c = []
    for n in range(3, max_possible_number + 1, 2):
        for l, c in itertools.product(range(height), range(width)):
            if puzzle[l][c] == TO_BE_FILLED:
                diag_indxs = list(diagonal_strips((l,c), height=height, width=width))
                # other cells in the diagonals containing n.
                other_cells_in_diagonal_strip = get_vars_at(diag_indxs)
                strip_contains_predecessor = Or([ cell == n-1
                    for cell in other_cells_in_diagonal_strip ])
                cnstrnt = Implies(board[l][c] == n, strip_contains_predecessor)
                diag_strip_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + distinct_c + instance_c + ortho_sum_c + ortho_strip_c  + diag_strip_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Zipline/007.a.htm by author Elliott Line
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 5,
            'puzzle':
            (  (13,0,0,6,6),
                (0,24,9,0,0),
                (0,0,0,0,0),
                (0,50,0,46,0),
                (29,0,0,0,29) ),

            'width': 5}
    solve_puzzle_zipline(**pars)
