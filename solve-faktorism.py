import itertools
from z3 import *
from puzzles_common import flatten

def solve_puzzle_faktorism(puzzle, *, height, width):
    # noted horizontally on the puzzle (on top, or at bottom)
    horizontal_factors = IntVector('hf', width)
    #noted vertically on the puzzle (on the left or the right)
    vertical_factors = IntVector('vf', height)

    _h_range_c = [ And(n >= 1, n <= width) for n in horizontal_factors ]
    _v_range_c = [ And(n >= 1, n <= height) for n in vertical_factors ]

    range_c = _h_range_c + _v_range_c

    distinct_c = [ Distinct(horizontal_factors), Distinct(vertical_factors) ]

    product_c = [ horizontal_factors[c] * vertical_factors[l] == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] > 0]

    s = Solver()

    s.add( range_c + distinct_c + product_c )

    s.check()
    m = s.model()
    return ([m[cell] for cell in horizontal_factors],
            [m[cell] for cell in vertical_factors])

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Faktorism/007.a.htm by author Iva Sallay
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 10,
            'puzzle':
            (
                (60,0,0,0,0,0,0,48,0,0),
                (0,0,0,0,0,32,0,0,0,0),
                (0,0,0,28,0,0,0,0,0,0),
                (0,50,0,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,10,0),
                (0,0,0,0,0,0,21,0,0,0),
                (0,0,0,0,6,0,0,0,0,0),
                (0,0,9,0,0,0,0,0,0,0),
                (0,0,0,0,0,0,0,0,0,18),
                (0,0,0,0,0,0,0,0,0,0),
                ),
            'width': 10}
    solve_puzzle_faktorism(**pars)
