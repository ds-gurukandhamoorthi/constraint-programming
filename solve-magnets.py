import itertools
from z3 import *
from more_z3 import IntMatrix, Exactly
from puzzles_common import transpose, flatten

# polarities
POSITIVE, NEUTRAL, NEGATIVE = 1, 0, -1

# what it means that the total of charges is count_
def coerce_charge(edges, polarity, count_):
        edges_with_given_polarity = [ edge == polarity
                for edge in edges ]
        return Exactly(*edges_with_given_polarity, count_)

# what it means to be a tile:
def coerce_tile(edge_1, edge_2):
    return Exactly(
        And(edge_1 == POSITIVE, edge_2 == NEGATIVE),
        And(edge_1 == NEGATIVE, edge_2 == POSITIVE),
        And(edge_1 == NEUTRAL, edge_2 == NEUTRAL),
        1)

# what it means to be neighbours in the board
def coerce_neigh(edge_1, edge_2):
    return Or([
        And(edge_1 == POSITIVE, edge_2 == NEGATIVE),
        And(edge_1 == NEGATIVE, edge_2 == POSITIVE),
        edge_1 == NEUTRAL,
        edge_2 == NEUTRAL,
        ])

# positive vertical
# -1 1 1  | 2
# 1 -1 -1 | 1
def solve_magnets(*, tiles, positive_horizontal, positive_vertical,
        negative_vertical, negative_horizontal, height, width):
    X = IntMatrix('m', nb_rows=height, nb_cols=width)

    # Let us concentrate on edge|pole|half of the tile|domino|magnet
    halves = flatten(X)
    # completeness
    complete_c = [ Or([edge == POSITIVE,
        edge == NEGATIVE,
        edge == NEUTRAL])
        for edge in halves ]

    assert len(positive_vertical) == len(X)
    pos_vertic_c = [ coerce_charge(row, POSITIVE, pos_v)
         for row, pos_v in zip(X, positive_vertical)
         if pos_v >= 0 ]

    assert len(negative_vertical) == len(X)
    neg_vertic_c = [ coerce_charge(row, NEGATIVE, neg_v)
         for row, neg_v in zip(X, negative_vertical)
         if neg_v >= 0 ]

    X_trans = transpose(X)

    assert len(positive_horizontal) == len(X_trans)
    pos_horiz_c = [ coerce_charge(row, POSITIVE, pos_h)
         for row, pos_h in zip(X_trans, positive_horizontal)
         if pos_h >= 0 ]

    assert len(negative_horizontal) == len(X_trans)
    neg_horiz_c = [ coerce_charge(row, NEGATIVE, neg_h)
         for row, neg_h in zip(X_trans, negative_horizontal)
         if neg_h >= 0 ]

    def horiz_tile(l, c):
        return X[l][c], X[l][c + 1]

    def vertic_tile(l, c):
        return X[l][c], X[l + 1][c]

    horiz_tiles_c = [ coerce_tile(*horiz_tile(l, c))
        for l, c in itertools.product(range(height), range(width))
        if tiles[l][c] == '>' ]

    vertic_tiles_c = [ coerce_tile(*vertic_tile(l, c))
        for l, c in itertools.product(range(height), range(width))
        if tiles[l][c] == 'v' ]

    # edge1 edge2 may not belong to the same magnet|tile
    horiz_neigh_c = [[ coerce_neigh(edge1, edge2)
            for edge1, edge2 in zip(row, row[1:]) ]
            for row in X ]
    horiz_neigh_c = flatten(horiz_neigh_c)

    vertic_neigh_c = [[ coerce_neigh(edge1, edge2)
            for edge1, edge2 in zip(row, row[1:]) ]
            for row in X_trans ]
    vertic_neigh_c = flatten(vertic_neigh_c)

    s = Solver()
    s.add(
            complete_c +
            pos_vertic_c + pos_horiz_c +
            neg_vertic_c + neg_horiz_c +
            horiz_tiles_c + vertic_tiles_c +
            horiz_neigh_c + vertic_neigh_c
            )

    s.check()
    m = s.model()
    return [ [ m[edge] for edge in row] for row in X ]

if __name__ == "__main__":

    pars = {'height': 5,
            'width': 6,
            'negative_horizontal': [3, -1, 2, -1, -1, 2],
            'negative_vertical': [-1, -1, -1, 1, 2],
            'positive_horizontal': [-1, 3, 1, -1, 1, 2],
            'positive_vertical': [-1, -1, -1, -1, 2],
            'tiles': [['>', ' ', 'v', 'v', 'v', 'v'],
                ['v', 'v', ' ', ' ', ' ', ' '],
                [' ', ' ', '>', ' ', 'v', 'v'],
                ['>', ' ', 'v', 'v', ' ', ' '],
                ['>', ' ', ' ', ' ', '>', ' ']],
            }
    solve_magnets(**pars)

    pars_2 = {'height': 9,
            'width': 10,
            'negative_horizontal': [3, 2, 4, 4, -1, 2, 4, -1, 0, -1],
            'negative_vertical': [-1, -1, 3, 5, -1, -1, -1, -1, -1],
            'positive_horizontal': [-1, -1, 4, -1, 4, 3, -1, 3, 1, -1],
            'positive_vertical': [-1, -1, 5, -1, 5, -1, -1, 2, 2],
            'tiles': [['v', '>', ' ', 'v', 'v', 'v', 'v', 'v', '>', ' '],
                [' ', '>', ' ', ' ', ' ', ' ', ' ', ' ', 'v', 'v'],
                ['>', ' ', 'v', '>', ' ', '>', ' ', 'v', ' ', ' '],
                ['v', 'v', ' ', 'v', '>', ' ', 'v', ' ', '>', ' '],
                [' ', ' ', 'v', ' ', '>', ' ', ' ', 'v', 'v', 'v'],
                ['>', ' ', ' ', 'v', 'v', '>', ' ', ' ', ' ', ' '],
                ['v', 'v', 'v', ' ', ' ', 'v', 'v', 'v', '>', ' '],
                [' ', ' ', ' ', '>', ' ', ' ', ' ', ' ', '>', ' '],
                ['>', ' ', '>', ' ', '>', ' ', '>', ' ', '>', ' ']],
            }
    solve_magnets(**pars_2)
