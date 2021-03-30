from z3 import *
import itertools
from collections import defaultdict

#transpose a square matrix
transpose = lambda m: list(zip(*m))

def IntSquareMatrix(prefix, sz):
    res = [[ Int(f'{prefix}_{i}_{j}') for i in range(sz)]
            for j in range(sz) ]
    return res

def coerce_eq(variabs, vals):
    variabs = list(variabs)
    vals = list(vals)
    assert len(variabs) == len(vals), 'Lengths of the variables and values must be equal for the intended coercing between them'
    return And([ var == v for var, v in zip(variabs, vals) ])

# Number of towers seen from left
# [4, 3, 5, 2, 1] -> 2  (tower of height 4 and tower of height 5 are seen)
def nb_towers_visible(heights):
    highest = 0
    res = 0
    for tower_height in heights:
        if tower_height > highest:
            highest = tower_height
            res += 1
    return res

def constrain_towers(tower_vars, tower_height, knowl):
    possiblts = knowl[tower_height]
    all_possiblts = [ coerce_eq(tower_vars, possib)
            for possib in possiblts ]
    return AtMost(*all_possiblts, 1)

def gen_knowl_dict(n):
    knowl_dict = defaultdict(list)
    for perm in itertools.permutations(list(range(1,n+1))):
        nb_towers = nb_towers_visible(perm)
        knowl_dict[nb_towers].append(perm)
    return knowl_dict

def solve_tower_puzzle(n, top, left, right, bottom, instance=None):
    knowl = gen_knowl_dict(n)
    X = IntSquareMatrix('h', n)
    X_trans = transpose(X)

    assert len(top) == len(left) == n
    assert len(right) == len(bottom) == n

    heights = itertools.chain(*X)
    heights_c = [ And(h >= 1, h <= n) for h in heights ]

    row_c = [ Distinct(row) for row in X ]
    col_c = [ Distinct(row) for row in X_trans ]

    left_c = [ constrain_towers(row, h, knowl)
            for row, h in zip(X, left) if h > 0 ]
    right_c = [ constrain_towers(row[::-1], h, knowl)
            for row, h in zip(X, right) if h > 0 ]

    top_c = [ constrain_towers(row, h, knowl)
            for row, h in zip(X_trans, top) if h > 0 ]
    bottom_c = [ constrain_towers(row[::-1], h, knowl)
            for row, h in zip(X_trans, bottom) if h > 0 ]

    s = Solver()
    s.add(heights_c + row_c + col_c +
           left_c + right_c + top_c + bottom_c)

    if instance is not None:
        for row_v, row in zip(X, instance):
            for var, value in zip(row_v, row):
                if value > 0:
                    s.add(var == value)

    s.check()
    m = s.model()

    res = [[ m[s] for s in row] for row in X]
    return res



if __name__ == "__main__":
    # top and bottom read the heights from left to right in the puzzle
    # left and right read the heights from top to bottom in the puzzle
    puzzle_easy = {
            'n': 5,
            'top': [2, 4, 1, 2, 5],
            'left': [2, 1, 3, 2, 4],
            'right': [3, 3, 2, 2, 1],
            'bottom': [3, 2, 3, 2, 1],
    }
    solve_tower_puzzle(**puzzle_easy)

    #put -1 or 0 when number of towers seen is not available
    puzzle_hard = {
            'n': 5,
            'top': [0, 2, 3, 0, 3],
            'left': [0, 0, 0, 2, 3],
            'right': [0, 0, 0, 0, 3],
            'bottom': [0, 0, 0, 2, 3],
            'instance': ((0,0,0,0,0),
                (0,0,0,0,0),
                (0,0,0,0,0),
                (0,0,0,0,0),
                (0,0,0,2,0)),
    }
    solve_tower_puzzle(**puzzle_hard)

    puzzle_extreme = {
            'n': 6,
            'top': [2, 0, 0, 2, 3, 0],
            'left': [0, 0, 2, 4, 3, 0],
            'right': [3, 3, 2, 2, 0, 3],
            'bottom': [3, 3, 0, 4, 0, 0],
            'instance': ((0,0,0,0,0,0),
                (0,0,0,0,0,0),
                (0,0,0,0,0,0),
                (0,0,1,0,0,0),
                (0,0,0,0,0,0),
                (0,0,0,0,0,0)),
    }
    solve_tower_puzzle(**puzzle_extreme)
