import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, rows_and_cols, get_same_block_indices
from more_itertools import pairwise

BLACK, WHITE = 1, 0

def solve_puzzle_campixu(*, height, width, cage_ids, horizontal_counts, vertical_counts, horizontal_runs, vertical_runs):
    board = IntMatrix('c', nb_rows=height, nb_cols=width)

    range_c = [ Xor(cell == BLACK, cell == WHITE)
            for cell in flatten(board) ]

    counts = vertical_counts + horizontal_counts

    count_c = []
    for line, cnt in zip(rows_and_cols(board), counts):
        black_cells = [ clr == BLACK for clr in line ]
        cnstrnt = Exactly(*black_cells, cnt)
        count_c.append(cnstrnt)

    at_ = lambda l, c : board[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    cages_inds = get_same_block_indices(cage_ids)

    #same color in each region/cage
    homogenous_cage_color_c = []
    for board_indices in cages_inds.values():
        if len(board_indices) > 1:
            vars_ = get_vars_at(board_indices)
            all_black = And([cell == BLACK for cell in vars_])
            all_white = And([cell == WHITE for cell in vars_])
            cnstrnt = Xor(all_white, all_black)
            homogenous_cage_color_c.append(cnstrnt)

    runs = vertical_runs + horizontal_runs

    run_c = []
    for line, nb_runs in zip(rows_and_cols(board), runs):
        extended_line = [WHITE] + list(line)
        starts_black_run = []
        for wnd in pairwise(extended_line):
            starts_black_run.append(And(wnd[0] == WHITE,
                wnd[1] == BLACK))
        cnstrnt = Exactly(*starts_black_run, nb_runs)
        run_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + count_c + homogenous_cage_color_c + run_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Campixu/007.a.htm by author Johannes Kestler
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 15,
            'vertical_counts': [6,6,7,2,4,2,12,5,9,3,7,8,4,9,1],
            'vertical_runs': [2,4,3,2,4,2,3,3,3,3,5,3,2,1,1],
            'horizontal_counts': [2,2,13,6,4,4,4,5,8,6,5,5,13,4,4],
            'horizontal_runs': [2,2,1,4,3,3,4,4,3,4,4,4,1,3,3],
            'cage_ids':
            ( (0,0,1,2,2,3,3,3,4,4,5,6,6,7,7),
                (0,0,8,9,2,2,10,3,4,11,12,13,14,15,15),
                (16,0,17,9,9,2,18,18,19,20,21,21,22,23,24),
                (16,16,17,25,25,26,26,27,28,28,21,29,22,23,24),
                (30,30,31,32,26,26,33,34,35,28,36,37,38,24,24),
                (30,39,40,41,26,42,43,34,35,35,44,45,46,24,24),
                (47,40,40,40,48,43,43,49,49,50,51,46,46,52,52),
                (53,54,40,55,56,57,43,49,50,50,51,51,46,58,58),
                (59,59,59,60,56,57,57,61,50,51,51,46,46,62,62),
                (63,63,64,65,66,66,61,61,67,68,68,68,69,70,70),
                (71,63,72,73,74,75,76,76,77,78,79,68,69,69,80),
                (63,63,72,73,74,74,77,77,77,77,81,81,69,80,80),
                (63,82,72,72,74,74,83,83,84,84,81,85,85,86,86),
                (87,88,88,89,89,90,90,90,90,91,92,85,93,94,94),
                (87,87,88,89,95,95,96,97,97,97,98,99,93,93,100)),
            'width': 15}
    solve_puzzle_campixu(**pars)
