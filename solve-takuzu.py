import itertools
from more_itertools import windowed
from z3 import *
from more_z3 import IntMatrix
from puzzles_common import flatten, transpose

BLACK, WHITE = 0, 1

def solve_puzzle_takuzu(puzzle, *, height, width):
    board = IntMatrix('b', nb_rows=height, nb_cols=width)

    assert width % 2 == 0, 'Width must be pair'
    assert height % 2 == 0,  'Height must be pair'

    vars_ = flatten(board)
    vals = flatten(puzzle)
    instance_c  = [ var == val for var, val in zip(vars_, vals)
            if val > -1 ]

    complete_c = [ Xor(cell == 0, cell == 1)
            for cell in flatten(board) ]

    # Equal number of 1s and 0s: so there are n/2 1s and n/2 0s
    _horiz_count_c = [ Sum(row) == width / 2
            for row in board ]
    _vertical_count_c = [ Sum(row) == height / 2
            for row in transpose(board) ]
    count_c = _horiz_count_c + _vertical_count_c

    # Rows or columns are unique
    def get_id(sequence):
        base = 2
        return Sum([val * base ** pos
           for pos, val in enumerate(sequence)])
    row_unique_c = [ Distinct([get_id(row) for row in board]) ]
    col_unique_c = [ Distinct([get_id(row) for row in transpose(board)]) ]

    # No more than 2 adjacent 1s or 0s
    def gen_adj_constraints(sequence):
        adjs = windowed(sequence, 3)
        # if three adjacent boxes are 0(resp 1) , sum is 0(resp 3).
        # Among the eight possibilities of three adjacent boxes
        return [ And(Sum(adj) != 0, Sum(adj) != 3)
               for adj in adjs ]
    _row_adj_c = flatten([ gen_adj_constraints(row) for row in board ])
    _col_adj_c = flatten([ gen_adj_constraints(row) for row in transpose(board) ])
    adj_c = _row_adj_c + _col_adj_c

    s = Solver()
    s.add(instance_c + complete_c + count_c + row_unique_c + col_unique_c + adj_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board]

if __name__ == "__main__":
    pars = {'height': 8,
            'width': 8,
            'puzzle': [

                [0, -1, -1, 1, -1, -1, -1, -1] ,
                [-1, 1, -1, -1, 0, -1, -1, 1] ,
                [-1, -1, -1, -1, -1, 1, -1, 1] ,
                [1, -1, -1, 0, -1, -1, -1, -1] ,
                [-1, -1, 0, -1, -1, 1, -1, -1] ,
                [-1, -1, 0, 1, -1, -1, -1, 0] ,
                [0, -1, -1, 1, -1, 1, 1, -1] ,
                [1, 0, -1, -1, -1, 0, -1, -1] ,
                ],
            }
    sol = solve_puzzle_takuzu(**pars)

    pars = {'height': 8,
            'width': 8,
            'puzzle': [
                [-1,-1,1,-1,-1,1,-1,-1],
                [-1,-1,1,-1,-1,-1,-1,-1],
                [0,-1,-1,0,-1,-1,-1,-1],
                [0,-1,-1,0,-1,-1,0,-1],
                [-1,-1,-1,-1,-1,-1,-1,-1],
                [-1,-1,-1,-1,-1,0,0,-1],
                [-1,1,-1,1,-1,-1,-1,1],
                [-1,-1,-1,-1,0,-1,0,-1],

                ],
            }
    sol = solve_puzzle_takuzu(**pars)
