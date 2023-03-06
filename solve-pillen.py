import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board, rows_and_cols
from more_itertools import windowed

BLACK, WHITE = 1, 0
PILL = WHITE # cell belongs to a pill
EMPTY = BLACK

def solve_puzzle_pillen(puzzle, *, height, width, horizontal_sums, vertical_sums, pill_count):

    # We give id to pills (each cell is empty or belong to a pill). id = 0 empty
    pill_id_board = IntMatrix('b_i', nb_rows=height, nb_cols=width)

    pill_id_range_c = [ And(cell >= 0 , cell <= pill_count)
            for cell in flatten(pill_id_board) ]

    pill_id_count_c = []
    # A given id for a pill (>=1, <=pill_count) can occur only 3 times. (the size of the pill). This is to avoid spilling of id to nearby cells, or scattering it elsewhere.
    # We don't add the constraint of contiguity here
    for given_id in range(1, pill_count + 1):
        cells_with_given_id = [ cell == given_id
                for cell in flatten(pill_id_board) ]
        cnstrnt = Exactly(*cells_with_given_id, 3)
        pill_id_count_c.append(cnstrnt)

    # There is only one pill with a given pill id
    pill_unicity_c = []
    pills = flatten([ list(windowed(line, 3))
            for line in rows_and_cols(pill_id_board) ])
    for given_id in range(1, pill_count + 1):
        pills_with_given_id = [
                coerce_eq(pill, (given_id, given_id, given_id))
                for pill in pills ]
        cnstrnt = Exactly(*pills_with_given_id, 1)
        pill_unicity_c.append(cnstrnt)

    pill_sum_c = []
    # given_id is also the sum of the three cells in a pill
    for given_id in range(1, pill_count + 1):
        sum_of_pill_with_given_id = Sum([ If(id_cell == given_id, cell, 0)
                for cell, id_cell in zip(flatten(puzzle), flatten(pill_id_board)) ])
        cnstrnt = sum_of_pill_with_given_id == given_id
        pill_sum_c.append(cnstrnt)

    sums = vertical_sums + horizontal_sums
    sums_c = []
    for values_, id_line, total in zip(rows_and_cols(puzzle), rows_and_cols(pill_id_board), sums):
        sum_of_line = Sum([ If(id_cell >= 1, value, 0)
                for value, id_cell in zip(values_, id_line) ])
        cnstrnt = sum_of_line == total
        sums_c.append(cnstrnt)


    s = Solver()

    s.add( pill_id_range_c + pill_id_count_c + pill_unicity_c + pill_sum_c + sums_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in pill_id_board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Pillen/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processed by z3.
    pars = {'height': 8,
            'horizontal_sums': [8, 3, 8, 3, 8, 5, 14, 6],
            'vertical_sums': [7, 8, 4, 18, 8, 2, 3, 5],
            'puzzle':(
                (4,4,3,2,3,2,2,1),
                (6,1,1,2,3,3,2,0),
                (0,0,2,4,4,3,3,2),
                (2,2,5,4,4,1,3,2),
                (2,1,3,3,0,1,6,2),
                (4,3,2,1,0,4,1,2),
                (3,2,4,0,1,1,2,0),
                (4,4,4,0,1,2,2,2)),
            'pill_count': 10,
            'width': 8}
    solve_puzzle_pillen(**pars)

