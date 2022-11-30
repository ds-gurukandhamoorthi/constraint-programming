import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, get_same_block_indices

EMPTY = 0

# strictly consecutive numbers (no repetition)
def gen_consecutive_numbers_constraint(lst):
    distinct_c = Distinct(lst)
    min_or_has_predecessor_c = []
    for i, elem in enumerate(lst):
        others = [ o_elem for j, o_elem in enumerate(lst)
                if j != i ]
        #No need to say Exactly 1. As we constrain elements to be distinct
        has_predecessor = Or([ oth == elem - 1 for oth in others ])
        is_min = And([ elem < oth for oth in others ])
        cnstrnt = Or(is_min, has_predecessor)
        min_or_has_predecessor_c.append(cnstrnt)
    return And(distinct_c , *min_or_has_predecessor_c)

def solve_puzzle_str8ts(*, height, width, order, instance, horiz_cages, vertic_cages):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    range_c = [ And(n >= 0, n <= order)
            for n in flatten(board) ]

    instance_c = []
    for vars_, val_row, hcages_row in zip(board, instance, horiz_cages):
        for var, value, hcage_id in zip(vars_, val_row, hcages_row):
            if hcage_id > 0: # cell white
                if value != EMPTY:
                    cnstrnt = var == value
                else:
                    cnstrnt = var != EMPTY #so there is no need for a separate cage_range_c constraint.
            else: # cell black
                if value != EMPTY:
                    cnstrnt = var == value
                else:
                    cnstrnt = var == EMPTY
            instance_c.append(cnstrnt)

    each_n_atmost_once_c = []
    # This is one way of expressing the constraint. The other way is to use distinct when not equal to 0... (as we did with the id_board idea)
    for n in range(1, order + 1):
        for line in rows_and_cols(board):
            occurrences_given_number = [ cell == n
                    for cell in line ]
            cnstrnt = AtMost(*occurrences_given_number, 1)
            each_n_atmost_once_c.append(cnstrnt)

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    # transposed
    trans_at_ = lambda l, c : board[c][l]
    def get_trans_vars_at(indices):
        return [ trans_at_(*ind) for ind in indices ]

    # numbers are consequent in a cage. (here: stripe of white cells)
    cage_consec_c = []
    h_cages_inds = get_same_block_indices(horiz_cages)

    del h_cages_inds[0] # Remove black cells

    for h_cage_indices in h_cages_inds.values():
        vars_ = get_vars_at(h_cage_indices)
        if len(vars_) > 1:
            cnstrnt = gen_consecutive_numbers_constraint(vars_)
            cage_consec_c.append(cnstrnt)

    v_cages_inds = get_same_block_indices(vertic_cages)

    del v_cages_inds[0] # Remove black cells

    for v_cage_indices in v_cages_inds.values():
        vars_ = get_trans_vars_at(v_cage_indices)
        if len(vars_) > 1:
            cnstrnt = gen_consecutive_numbers_constraint(vars_)
            cage_consec_c.append(cnstrnt)


    s = Solver()

    s.add( range_c + instance_c + each_n_atmost_once_c + cage_consec_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Straights/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 9,
            'order': 9,
            'instance':
            (  (9,6,8,1,0,0,0,4,0),
                (0,0,0,0,4,0,0,7,0),
                (5,0,0,0,3,0,0,0,0),
                (0,0,0,0,0,4,6,0,0),
                (0,0,0,0,0,0,0,0,0),
                (3,0,0,0,5,8,0,0,0),
                (0,0,0,0,0,0,0,5,0),
                (0,0,5,0,0,0,4,1,0),
                (0,7,0,0,0,0,0,0,1)),
            'horiz_cages':
            ( (0,1,1,1,1,1,1,1,1),
                (2,2,0,0,3,3,3,0,0),
                (4,0,0,5,5,5,0,0,6),
                (7,0,8,8,8,8,0,9,9),
                (0,10,10,10,0,11,11,11,0),
                (12,12,0,13,13,13,13,0,14),
                (15,0,0,16,16,16,0,0,17),
                (0,0,18,18,18,0,0,19,19),
                (20,20,20,20,20,20,20,20,0)),
            'vertic_cages':
            ( (0,1,1,1,0,2,2,0,3),
                (4,4,0,0,5,5,0,0,6),
                (7,0,0,8,8,0,0,9,9),
                (10,0,11,11,11,11,11,11,11),
                (12,12,12,12,0,13,13,13,13),
                (14,14,14,14,14,14,14,0,15),
                (16,16,0,0,17,17,0,0,18),
                (19,0,0,20,20,0,0,21,21),
                (22,0,23,23,0,24,24,24,0)),
            'width': 9}
    solve_puzzle_str8ts(**pars)
