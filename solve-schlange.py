import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose, inside_board, rows_and_cols
from puzzles_common import ortho_neighbours as neighbours

EMPTY = 0

def solve_puzzle_schlange(*, height, width, vertical_counts, horizontal_counts, extremities):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    assert sum(horizontal_counts) == sum(vertical_counts)
    nb_occupied_cells = sum(horizontal_counts)
    MAX = nb_occupied_cells


    range_c = [ And(cell >= 0, cell <= nb_occupied_cells)
            for cell in flatten(board) ]

    at_ = lambda l, c : board[l][c]
    start_index, end_index = extremities
    extremities_c = [ at_(*start_index) == 1, at_(*end_index) == MAX ]


    #Note: distinct_c is defined differently than in solve-tracks.py

    # Every occupied cell is at a given 'distance' to the start.
    # No other cell has the same distance
    distinct_c = []
    for dist in range(1, MAX + 1):
        cells_with_given_dist = [ cell == dist for cell in flatten(board) ]
        cnstrnt = Exactly(*cells_with_given_dist, 1)
        distinct_c.append(cnstrnt)

    counts = vertical_counts + horizontal_counts

    count_c = []
    for line, cnt in zip(rows_and_cols(board), counts):
        occupied_cells = [ n >= 1 for n in line ]
        cnstrnt = Exactly(*occupied_cells, cnt)
        count_c.append(cnstrnt)

    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    def gen_consecutive_nums_constraint(l, c):
        geom = { 'height': height, 'width': width }
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, **geom) ]
        neighs = get_vars_at(val_neighs)

        var = at_(l, c) #content of current cell
        one_adj_cell_is_consec_c = Exactly(*[ adj == var + 1 for adj in neighs ], 1)
        current_cell_is_max_c = var == MAX
        unoccupied_c = var == EMPTY
        return Or(unoccupied_c, current_cell_is_max_c, one_adj_cell_is_consec_c)

    # constraint forcing one of the adjacent cells to be the 'successor'
    successor_c = [ gen_consecutive_nums_constraint(l, c)
            for l, c in itertools.product(range(height), range(width)) ]

    # To describe that the snake must have a width of 1, we can say any square in the grid can have at most 3 black squares. This would disallow the snake doubling-back or touching orthogonally
    snake_width_c = []

    def gen_proximity_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        black_cells_in_a_square = [ at_(*cell) >= 1 for cell in val_cells_in_square ]
        # The following constraint would in a context-free manner force the snake to have a width of 1
        return AtMost(*black_cells_in_a_square, 3)

    # In generating constraints we wander towards right and towards bottom
    # So : height - 1, width - 1
    snake_width_c = [ gen_proximity_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    # when there is a right-angled block :
    # 23
    # 10
    # it is made by three consecutive numbers.
    # this is like the simple-math exercise asking to find three consecutive numbers given their sum: n + (n+1) + (n+2)
    def gen_right_angle_turn_constraints(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        vars_square = get_vars_at(val_cells_in_square)
        assert len(vars_square) == 4
        # we use the fact that EMPTY == 0. Otherwise If(cell != EMPTY, cell, 0) etc
        total = Sum(vars_square)
        count_ = Sum([If(cell == EMPTY, 0, 1)
            for cell in vars_square])
        right_angled_turn = count_ == 3
        presence_each_number = []
        for i in (-1, 0, 1):
            cnstrnt = Or([var == total/3 + i for var in vars_square])
            presence_each_number.append(cnstrnt)
        return Implies(right_angled_turn , And(presence_each_number))

    right_angle_turn_c = [ gen_right_angle_turn_constraints(l, c)
        for l, c in itertools.product(range(height - 1), range(width - 1)) ]

    def gen_diagonal_constraint(l, c):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=height, width= width)]
        vars_square = get_vars_at(val_cells_in_square)
        assert len(vars_square) == 4
        a, b, c, d = vars_square
        # a b
        # c d
        # we cannot have a and d (resp b and c) occupied without them being joined by another occupied cell
        # example: we cannot have:
        #  5  0
        #  0  17
        diag_1_c = Implies( And(a >= 1, d >= 1), Or( b >=1, c >= 1))
        diag_2_c = Implies( And(b >= 1, c >= 1), Or( a >=1, d >= 1))
        return And(diag_1_c, diag_2_c)

    diagonal_touch_c = [ gen_diagonal_constraint(l, c)
            for l, c in itertools.product(range(height - 1), range(width - 1)) ]


    s = Solver()

    s.add( range_c + extremities_c + distinct_c +  successor_c + snake_width_c + right_angle_turn_c + diagonal_touch_c + count_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Schlange/007.a.htm by author Valery Rubantsev
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processed by z3.
    pars = {'height': 11,
            'vertical_counts': [4, 6, 3, 3, 8, 5, 3, 1, 5, 1, 3],
            'horizontal_counts': [4, 2, 2, 9, 2, 5, 5, 5, 2, 2, 4],
            'extremities': ( (2, 0), (10, 1) ),
            'width': 11}
    solve_puzzle_schlange(**pars)

