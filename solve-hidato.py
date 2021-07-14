from z3 import *
import itertools
from more_z3 import IntMatrix, Exactly
from puzzles_common import inside_board

def neighbours(l, c):
    for i, j in itertools.product([-1, 0, 1], repeat=2):
        if (i, j) != (0, 0):
            yield(l + i, c + j)

def solve_hidato(puzzle, *, order, maximum):
    X = IntMatrix('n', order, order)

    vars_ = list(itertools.chain(*X))
    vals = list(itertools.chain(*puzzle))

    # occupied cells == cells belonging to the solution
    # filled cells == cells already filled
    # a filled cell is a occupied cell.
    # An occupied cell would be a filled cell at the end of the solution

    # occup == -1 for holes, and unoccupied cells
    occupied_cells = [ cell for cell, occup in zip(vars_, vals)
            if occup > -1 ]

    range_c = [ And(cell >= 1, cell <= maximum)
            for cell in occupied_cells ]

    distinct_c = [ Distinct(occupied_cells) ]

    # cell == 0 for cells not yet filled
    # So cell > 0 contains cells already filled
    instance_c = [cell == val for cell, val in zip(vars_, vals)
            if val > 0]

    at_ = lambda l, c : X[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    def gen_consecutive_nums_constraint(l, c):
        val_neighs = [ neigh for neigh in neighbours(l, c)
                if inside_board(neigh, height=order, width=order) ]
        neighs = get_vars_at(val_neighs)
        occupied_neighs = set(neighs).intersection(occupied_cells)
        var = at_(l, c) #content of current cell
        one_adj_cell_is_consec_c = Exactly(*[ adj == var + 1 for adj in occupied_neighs ], 1)
        current_cell_is_max_c = var == maximum
        return Or(current_cell_is_max_c, one_adj_cell_is_consec_c)

    consecutive_c = []

    for l, row_vals in enumerate(puzzle):
        for c, val in enumerate(row_vals):
            if val >= 0:
                constrnt = gen_consecutive_nums_constraint(l, c)
                consecutive_c.append(constrnt)


    s = Solver()
    s.add( range_c + instance_c + distinct_c + consecutive_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in X]


if __name__ == "__main__":
    pars = {
            'puzzle': ((0,33,35,0,0,-1,-1,-1),
                (0,0,24,22,0,-1,-1,-1),
                (0,0,0,21,0,0,-1,-1),
                (0,26,0,13,40,11,-1,-1),
                (27,0,0,0,9,0,1,-1),
                (-1,-1,0,0,18,0,0,-1),
                (-1,-1,-1,-1,0,7,0,0),
                (-1,-1,-1,-1,-1,-1,5,0)),
            'order': 8,
            'maximum': 40,
            }

    solve_hidato(**pars)
