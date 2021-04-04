import itertools
from z3 import *

#transpose a matrix
transpose = lambda m: list(zip(*m))

def flatten(list_of_lists):
    return list(itertools.chain(*list_of_lists))

def IntMatrix(prefix, nb_rows, nb_cols):
    res = [[ Int(f'{prefix}_{i}_{j}') for j in range(nb_cols)]
                            for i in range(nb_rows) ]
    return res

# Exactly(1) -> False, Exactly(0) -> True, Exactly(2) -> False.
# As would PbEq([ (p, 1) for p in [] ], 1)
def Exactly(*args):
    assert len(args) >= 1, 'Non empty list of arguments expected'
    return PbEq([
        (arg, 1) for arg in args[:-1]],
        args[-1])

def neighbours(index_):
    up, down, left, right = (1, 1, 1, 1)
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]

# index = line, column
def inside_board(index_lc, *, height, width):
    l, c = index_lc
    return (0 <= l < height) and (0 <= c < width)

# We choose tree = 1.. tent = -1, -2.. we use this id later for couplings
def preprocess(board, *, height, width):
    def get_unique_tree_ids(l, c):
        if board[l][c] == 0:
            return 0
        return l * width + c  + 1
        # we add 1 so that the first tree is not 0. -0 = 0
        # as we use negation to distinguish between trees and tents
    res = [[ get_unique_tree_ids(l, c) for c in range(width) ]
            for l in range(height) ]
    return res

def solve_tents(board, *, height, width, horizontal_tents, vertical_tents):
    preprocessed = preprocess(board, height=height, width=width)
    X = IntMatrix('t', nb_rows=height, nb_cols=width)
    at_ = lambda l, c: X[l][c]
    is_tree = lambda l, c: preprocessed[l][c] > 0
    # the coupling between a tree and a tent is unique. Think tile|domino
    def gen_coupling_constraints(l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        couplings = [ X[l][c] == -at_(*cell) for cell in val_neighs ]
        # we don't add constraint that it is unoccupied by a tree
        # it's taken care by another set of constraints
        # return Exactly(*couplings, 1)
        return Exactly(*couplings, 1)

    # No two tents can be adjacent to each other.
    # None of the 8 directions. (think: King's move in chess).
    # The description above is the tent's point of view
    # If we take the board's point of view:
    # A square of 4 cells can contain at most 1 tree
    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        # cell < 0 : we have encoded as tent
        tents_in_a_square = [ at_(*cell) < 0 for cell in val_cells_in_square ]
        return AtMost(*tents_in_a_square, 1)

    def coerce_nb_tents(cells, count_):
        tents = [ cell < 0 for cell in cells ]
        return Exactly(*tents, count_)

    MAX = height * width

    complete_c = [ And(-MAX < cell, cell < MAX)
            for cell in flatten(X) ]

    coupling_c = [ gen_coupling_constraints(l, c)
            for l, c in itertools.product(range(height), range(width))
            if is_tree(l, c)]

    instance_c = [ at_(l, c) == preprocessed[l][c]
            for l, c in itertools.product(range(height), range(width))
            if preprocessed[l][c] > 0 ]

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    tree_proximity_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    NB_TREES = sum( cell > 0 for cell in flatten(preprocessed) )
    same_number_trees_tents_c = [ coerce_nb_tents(flatten(X), NB_TREES) ]

    # vertical tents means nb tents in each line. Noted vertically on the board
    # on the left or right side
    assert len(vertical_tents) == height == len(X)
    row_sums_c = [ coerce_nb_tents(row, count_v)
            for row, count_v in zip(X, vertical_tents) ]

    X_trans = transpose(X)
    # horizontal tents means nb tents in each line. Noted horizontally on the board
    # at the bottom of the board or top of the board
    assert len(horizontal_tents) == width == len(X_trans)
    # row in X_trans means col in X
    col_sums_c = [ coerce_nb_tents(row, count_h)
            for row, count_h in zip(X_trans, horizontal_tents) ]

    # NOTE: if ever col_sums or row_sums are partially erased to add difficulty.
    # use -1. and add here if count_h >= 0

    s = Solver()
    s.add(complete_c + instance_c +
           coupling_c + tree_proximity_c +
           same_number_trees_tents_c +
           row_sums_c + col_sums_c)
    m = s.model()
    return [ [ m[cell] for cell in row ] for row in X ]

if __name__ == "__main__":
    pars = {
            'board': [[0, 0, 0, 0, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, 0, 1, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 1, 1, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0, 0]],
            'height': 7,
            'width': 9,
            'horizontal_tents': [3, 0, 2, 1, 1, 1, 1, 1, 2],
            'vertical_tents': [3, 1, 3, 0, 4, 0, 1],
            }

    preprocess(pars['board'], height=pars['height'],
            width=pars['width'])

    solve_tents(**pars)

    pars = {
            'board': [[0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
                [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1],
                [0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0],
                [0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
                [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]],
            'height': 15,
            'width': 15,
            'horizontal_tents': [2, 4, 3, 3, 3, 4, 2, 2, 3, 4, 1, 7, 0, 4, 3],
            'vertical_tents': [2, 4, 1, 5, 2, 3, 3, 4, 2, 4, 2, 5, 2, 4, 2],
            }
    solve_tents(**pars)
