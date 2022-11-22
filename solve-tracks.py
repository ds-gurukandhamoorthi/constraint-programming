from z3 import *
import itertools
from more_z3 import IntMatrix, Exactly
from puzzles_common import transpose, inside_board
from puzzles_common import ortho_neighbours as neighbours

def solve_tracks(*, tracks, start_index, end_index, horizontal_clues, vertical_clues, height, width):
    X = IntMatrix('t', nb_rows=height, nb_cols=width)
    assert sum(horizontal_clues) == sum(vertical_clues)
    nb_occupied_cells = sum(horizontal_clues)
    MAX = nb_occupied_cells

    cells = list(itertools.chain(*X))
    range_c = [ And(n >= 0, n <= nb_occupied_cells)
            for n in cells ]

    at_ = lambda l, c : X[l][c]
    extremities_c = [ at_(*start_index) == 1, at_(*end_index)== MAX ]
    for index_, pattern in tracks:
        l, c = index_
        bottom, left, top, right = map(int, list(pattern))
        bottom, left, top, right = bottom == 1, left == 1, top == 1, right == 1
        if index_ == start_index:
            # the starting track is the leftmost
            # so it has no left
            if bottom:
                nxt = l + 1, c
            elif top:
                nxt = l - 1, c
            elif right:
                nxt = l, c + 1
            curr_var = at_(*index_)
            nxt_var = at_(*nxt)
            extremities_c.append( nxt_var == curr_var + 1 )
        elif index_ == end_index:
            # the ending track is the bottommost
            # so it has no bottom
            if top:
                prv = l - 1, c
            if right:
                prv = l, c + 1
            if left:
                prv = l, c - 1
            curr_var = at_(*index_)
            prv_var = at_(*prv)
            extremities_c.append( curr_var == prv_var + 1 )


    X_trans = transpose(X)

    # Exactly count_ occupied (> 0) cells in each row
    row_sums_c = [ Exactly(*[cell > 0 for cell in row], count_)
            for row, count_ in zip(X, vertical_clues) ]

    row_sums_c = [ Exactly(*[cell > 0 for cell in row], count_)
            for row, count_ in zip(X, vertical_clues) ]

    col_sums_c = [ Exactly(*[cell > 0 for cell in row], count_)
            for row, count_ in zip(X_trans, horizontal_clues) ]

    # we give unique_id to unoccupied cell. for using Distinct on occupied cells
    distinct_c = Distinct([If(cell > 0, cell, -i) for i, cell in enumerate(cells, 1)])
    # Every occupied cell is at a given 'distance' to the start.
    # No other cell has the same distance
    distinct_c = [ distinct_c ]

    def get_adj_track_indices(index_, pattern):
        l, c = index_
        bottom, left, top, right = map(int, list(pattern))
        bottom, left, top, right = bottom == 1, left == 1, top == 1, right == 1
        res = []
        if left:
            # the starting track is the leftmost
            if index_ != start_index:
                res.append((l, c - 1))
        if right:
            res.append((l, c + 1))
        if top:
            res.append((l - 1, c))
        if bottom:
            # the ending track is the bottommost
            if index_ != end_index:
                res.append((l + 1, c))
        res.insert(1, index_)
        return res

    at_ = lambda l, c : X[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    def coerce_sequential(vars_):
        curr, *succs = vars_
        ascending_c = And([ nxt == curr + i for i, nxt in enumerate(succs, 1) ])
        descending_c = And([ nxt == curr - i for i, nxt in enumerate(succs, 1) ])
        return Or(ascending_c, descending_c)

    # constraint forcing parts of the tracks to be in ascending or descending order
    sequential_c = []
    for index_, pattern in tracks:
        inds = get_adj_track_indices(index_, pattern)
        successive_track_vars = get_vars_at(inds)
        cnstrnt = coerce_sequential(successive_track_vars)
        sequential_c.append(cnstrnt)
    # The start and end track produces an absurd condition. but it would be weeded out by other constraints.

    def gen_consecutive_nums_constraint(l, c):
        geom = { 'height': height, 'width': width }
        val_neighs = [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, **geom) ]
        neighs = get_vars_at(val_neighs)

        var = at_(l, c) #content of current cell
        one_adj_cell_is_consec_c = Exactly(*[ adj == var + 1 for adj in neighs ], 1)
        current_cell_is_max_c = var == MAX
        unoccupied_c = var == 0
        return Or(unoccupied_c, current_cell_is_max_c, one_adj_cell_is_consec_c)

    # constraint forcing one of the adjacent cells to be the 'successor'
    successor_c = [ gen_consecutive_nums_constraint(l, c)
            for l, c in itertools.product(range(height), range(width)) ]


    s = Solver()
    s.add( range_c + extremities_c + row_sums_c + col_sums_c + distinct_c
            + sequential_c + successor_c)

    s.check()
    m = s.model()

    res = [[ m[s] for s in row] for row in X]
    return res


if __name__ == "__main__":
    pars = {'end_index': (14, 10),
            'height': 15,
            'horizontal_clues': [4, 5, 4, 5, 6, 1, 4, 4, 9, 11, 4, 3, 4, 7, 6],
            'start_index': (6, 0),
            'tracks': [((0, 1), '1100'),
                ((1, 3), '0011'),
                ((1, 6), '0110'),
                ((1, 8), '0101'),
                ((3, 2), '0101'),
                ((3, 3), '0101'),
                ((5, 9), '0011'),
                ((6, 0), '0101'),
                ((8, 13), '0101'),
                ((10, 14), '1010'),
                ((11, 14), '1010'),
                ((14, 10), '1100')],
            'vertical_clues': [8, 10, 6, 8, 2, 4, 8, 4, 3, 6, 7, 3, 4, 1, 3],
            'width': 15}

    solve_tracks(**pars)

    pars ={'end_index': (6, 7),
            'height': 7,
            'horizontal_clues': [2, 4, 1, 3, 3, 2, 4, 5, 5, 2],
            'start_index': (1, 0),
            'tracks': [((1, 0), '0110'), ((2, 3), '1010'), ((6, 7), '1001')],
            'vertical_clues': [2, 4, 6, 9, 5, 3, 2],
            'width': 10}

    solve_tracks(**pars)
