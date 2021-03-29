from z3 import *
import itertools
from collections import defaultdict

#transpose a square matrix
transpose = lambda m: zip(*m)

def IntSquareMatrix(prefix, sz):
    res = [[ Int(f'{prefix}_{i}_{j}') for i in range(sz)]
            for j in range(sz) ]
    return res

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
    constrain_single = lambda possib: And([twr == h
        for twr, h in zip(tower_vars, possib)])
    all_possiblts = [constrain_single(possib) for possib in possiblts]
    return Or(all_possiblts)

def gen_knowl_dict(n):
    knowl_dict = defaultdict(list)
    for perm in itertools.permutations(list(range(1,n+1))):
        nb_towers = nb_towers_visible(perm)
        knowl_dict[nb_towers].append(perm)
    return knowl_dict

def solve_tower_puzzle(n, top, left, right, bottom):
    knowl = gen_knowl_dict(n)
    X = IntSquareMatrix('h', 5)

    left_c = [constrain_towers(row, h, knowl)
            for row, h in zip(X, left) if h > 0]
    right_c = [constrain_towers(row[::-1], h, knowl)
            for row, h in zip(X, right) if h > 0]

    X_trans = transpose(X)
    top_c = [constrain_towers(row, h, knowl)
            for row, h in zip(X_trans, top) if h > 0]
    bottom_c = [constrain_towers(row[::-1], h, knowl)
            for row, h in zip(X_trans, bottom) if h > 0]

    s = Solver()
    s.add(left_c + right_c + top_c + bottom_c)

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

    #for difficult_puzzles
    #FIXME: add possiblity to add the value of some heights (a little like the sudoku instance_c as in the official example)
