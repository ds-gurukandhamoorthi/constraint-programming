import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board
from more_itertools import pairwise
from puzzles_common import ortho_neighbours as neighbours

BLACK, WHITE = 0, 1

def solve_puzzle_hitori(puzzle, *, height, width):
    color_board = IntMatrix('c', nb_rows=height, nb_cols=width)

    def get_id(l, c):
        return -(l * width + c + 1)

    id_board = [[get_id(l, c) for c in range(width)]
            for l in range(height)]

    color_range_c = [Xor(clr == BLACK, clr == WHITE)
            for clr in flatten(color_board)]

    row_distinct_c = []
    for clrs, vals, ids in zip(color_board, puzzle, id_board):
        vals_or_ids = ([ If(clr==BLACK, id_, val) for clr, val, id_ in zip(clrs, vals, ids) ])
        cnstrnt = Distinct(vals_or_ids)
        row_distinct_c.append(cnstrnt)

    col_distinct_c = []
    for clrs, vals, ids in zip(transpose(color_board), transpose(puzzle), transpose(id_board)):
        vals_or_ids = ([ If(clr==BLACK, id_, val) for clr, val, id_ in zip(clrs, vals, ids) ])
        cnstrnt = Distinct(vals_or_ids)
        col_distinct_c.append(cnstrnt)

    distinct_c = row_distinct_c + col_distinct_c

    row_adj_c = []
    for clrs in color_board:
        for (c1, c2) in pairwise(clrs):
            cnstrnt = Or(c1 != BLACK, c2 != BLACK)
            row_adj_c.append(cnstrnt)

    col_adj_c = []
    for clrs in transpose(color_board):
        for (c1, c2) in pairwise(clrs):
            cnstrnt = Or(c1 != BLACK, c2 != BLACK)
            col_adj_c.append(cnstrnt)

    adj_c = row_adj_c + col_adj_c

    range_num_c = []
    # We assign number to each cell (so as to enforce 'connectivity' between white cells)
    num_board = IntMatrix('n', nb_rows=height, nb_cols=width)
    for clr_row, num_row in zip(color_board, num_board):
        for clr, num in zip(clr_row, num_row):
            cnstrnt = (clr == BLACK) == (num == -1)
            range_num_c.append(cnstrnt)
            cnstrnt = (clr == WHITE) == (num >= 0)
            range_num_c.append(cnstrnt)

    nums = flatten(num_board)
    single_start_c = [ Exactly(*[n == 0 for n in nums], 1) ]

    num_at_ = lambda l, c: num_board[l][c]
    def gen_predecessor_constraints(l, c):
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, height=height, width=width)]
        # the current cell
        cell = num_at_(l,c)
        val_neigh_cells = [num_at_(*cell) for cell in val_neighs]
        one_neigh_is_predecessor = AtLeast(*[And(neigh_cell >= 0, neigh_cell == cell - 1) for neigh_cell in val_neigh_cells], 1)
        cnstrnt = (cell > 0) == one_neigh_is_predecessor
        return cnstrnt

    predecessor_c = [ gen_predecessor_constraints(l, c)
        for l, c in itertools.product(range(height), range(width)) ]

    # connectivity constraint as proposed by Gerhard van der Knijff in 'Solving and generating puzzles with a connectivity constraint'
    connectivity_c = range_num_c + single_start_c + predecessor_c

    opt = Optimize()

    opt.add(color_range_c + distinct_c + adj_c + connectivity_c)

    # Number of walls we don't blacken (that we leave as it is)
    reward = Int('reward')
    opt.add(reward == Sum(flatten(color_board)))
    h = opt.maximize(reward)

    opt.check()
    m = opt.model()

    return [ [m[cell] for cell in row] for row in color_board ]

if __name__ == "__main__":
    pars = {'height': 12,
            'puzzle': [[19, 1, 2, 17, 16, 9, 9, 14, 5, 17, 7, 13, 1, 19, 4, 17, 2, 11, 11, 16],
                [7, 13, 19, 10, 5, 11, 12, 17, 7, 20, 5, 9, 18, 8, 9, 1, 16, 3, 4, 14],
                [3, 5, 10, 20, 7, 11, 20, 12, 11, 13, 1, 2, 4, 14, 9, 18, 2, 5, 7, 8],
                [12, 8, 7, 15, 6, 20, 6, 9, 14, 20, 9, 16, 5, 1, 16, 19, 19, 17, 1, 15],
                [7, 18, 14, 18, 16, 13, 16, 3, 5, 9, 10, 7, 9, 17, 5, 19, 19, 1, 11, 4],
                [9, 13, 2, 12, 13, 16, 8, 10, 16, 9, 3, 20, 15, 10, 11, 17, 17, 20, 2, 18],
                [17, 15, 3, 20, 6, 19, 9, 16, 3, 8, 10, 1, 2, 18, 12, 16, 17, 7, 5, 10],
                [20, 18, 18, 3, 19, 10, 16, 19, 3, 12, 5, 7, 1, 16, 6, 12, 9, 13, 7, 10],
                [10, 5, 3, 15, 19, 6, 20, 7, 4, 11, 20, 15, 5, 16, 2, 9, 9, 8, 4, 17],
                [5, 4, 17, 1, 13, 7, 11, 9, 9, 4, 11, 16, 20, 19, 13, 18, 6, 18, 2, 19],
                [10, 14, 6, 18, 8, 6, 4, 16, 9, 12, 11, 19, 15, 10, 2, 12, 16, 2, 16, 15],
                [19, 4, 6, 13, 18, 16, 11, 5, 7, 17, 7, 20, 9, 1, 14, 2, 11, 18, 3, 6]],
            'width': 20}
    solve_puzzle_hitori(**pars)
