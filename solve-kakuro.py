from z3 import *
import itertools
from more_z3 import IntMatrix
from puzzles_common import get_same_block_indices

def solve_kakuro(horiz_cages, vertic_cages, horiz_clues, vertic_clues, *, order):
    X = IntMatrix('n', order, order)

    at_ = lambda l, c : X[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]


    # Look for any discrepancies between horiz and vertic occupancies.
    for h_row, v_row in itertools.zip_longest(horiz_cages, vertic_cages):
        for l, c in itertools.zip_longest(h_row, v_row):
            if l < 0 or c < 0:
                assert (l, c) == (-1, -1)

    vars_ = itertools.chain(*X)
    # We have already verified that horiz_cages and vertic_cages have same occupancies
    occupancy = itertools.chain(*horiz_cages)
    # digit
    range_c = [ And(cell >=1, cell <= 9)
           for cell, occup in zip(vars_, occupancy)
               if occup > -1]

    h_cage_c = []
    h_cages_inds = get_same_block_indices(horiz_cages)
    for h_clue_ind, h_cage_indices in h_cages_inds.items():
        if h_clue_ind > -1: # cell is occupied
            vars_ = get_vars_at(h_cage_indices)
            cnstrnt = And(Distinct(vars_), Sum(vars_) == horiz_clues[h_clue_ind])
            h_cage_c.append(cnstrnt)

    v_cage_c = []
    v_cages_inds = get_same_block_indices(vertic_cages)
    for v_clue_ind, v_cage_indices in v_cages_inds.items():
        if v_clue_ind > -1: # cell is occupied
            vars_ = get_vars_at(v_cage_indices)
            cnstrnt = And(Distinct(vars_), Sum(vars_) == vertic_clues[v_clue_ind])
            v_cage_c.append(cnstrnt)

    s = Solver()
    s.add(range_c + h_cage_c + v_cage_c)

    s.check()
    m = s.model()

    res = [[ m[s] for s in row] for row in X]
    return res


if __name__ == "__main__":
    pars = {
            'order': 8,
            'horiz_cages': ((-1,-1,-1,-1,-1,-1,-1,-1),
                (-1,0,0,-1,-1,1,1,1),
                (-1,2,2,-1,3,3,3,3),
                (-1,4,4,4,4,4,-1,-1),
                (-1,-1,5,5,-1,6,6,-1),
                (-1,-1,-1,7,7,7,7,7),
                (-1,8,8,8,8,-1,9,9),
                (-1,10,10,10,-1,-1,11,11),
                ),

            'horiz_clues' : [16,24,17,29,35,7,8,16,21,5,6,3],

            'vertic_cages': ((-1,-1,-1,-1,-1,-1,-1,-1),
                (-1,0,2,-1,-1,7,8,10),
                (-1,0,2,-1,5,7,8,10),
                (-1,0,2,4,5,7,-1,-1),
                (-1,-1,2,4,-1,7,9,-1),
                (-1,-1,-1,4,6,7,9,11),
                (-1,1,3,4,6,-1,9,11),
                (-1,1,3,4,-1,-1,9,11),
                ),


                'vertic_clues' : [23,11,30,10,15,17,7,27,12,12,16,7],
                }

    solve_kakuro(**pars)
