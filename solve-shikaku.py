import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten

def get_possible_rectangles_at(cell, *, height, width, rect_area):
    cell_row, cell_col = cell

    rect_topleft_row = Int('rect_topleft_row')
    rect_topleft_col = Int('rect_topleft_col')

    rect_width, rect_height = Ints('rect_width rect_height')

    range_rect_c = [
            rect_height >= 1,
            rect_width >= 1,
            rect_height <= height, #can't exceed board
            rect_width <= width,
            ]

    rect_position_c = [
            rect_topleft_row >= 0,
            rect_topleft_col >= 0,
            rect_topleft_col + rect_width <= width,
            rect_topleft_row + rect_height <= height,
            ]

    rect_contains_cell_c = [
            cell_row >= rect_topleft_row,
            cell_col >= rect_topleft_col,
            cell_row < rect_topleft_row + rect_height,
            cell_col < rect_topleft_col + rect_width,
            ]

    area_c = [ rect_height * rect_width == rect_area ]

    rect_vars = (rect_topleft_row, rect_topleft_col, rect_width, rect_height)

    res = []
    s = Solver()
    s.add(range_rect_c + area_c + rect_position_c + rect_contains_cell_c)
    while s.check() == sat:
        m = s.model()
        solution = tuple(m[var].as_long() for var in rect_vars)
        res.append(solution)
        avoid_seen_c = Not(coerce_eq(rect_vars, solution))
        s.add(avoid_seen_c)
    return res

def get_indices_in_rect(rect):
    topleft_row, topleft_col, width, height = rect
    for l_offset, c_offset in itertools.product(range(height), range(width)):
        yield (topleft_row + l_offset, topleft_col + c_offset)

def solve_puzzle_shikaku(puzzle, *, height, width):
    X = IntMatrix('r', nb_rows=height, nb_cols=width)

    assert sum(flatten(puzzle)) == height * width, "Sum of the areas of all rectangles must be equal to board area"

    at_ = lambda l, c: X[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    def get_unique_rect_id(l, c):
        return l * width + c  + 1

    rectangle_area_c = []

    for l, c in itertools.product(range(height), range(width)):
        rect_area = puzzle[l][c]
        if rect_area > 0:
            rect_id = get_unique_rect_id(l, c)
            rects = get_possible_rectangles_at((l,c), height=height, width=width, rect_area=rect_area)
            rectangle_configs_with_this_id = []
            for rect in rects:
                indices = list(get_indices_in_rect(rect))
                rect_vars = get_vars_at(indices)
                # This is like "coloring" the rectangle with id
                cnstrnt = coerce_eq(rect_vars, [rect_id] * len(rect_vars))
                rectangle_configs_with_this_id.append(cnstrnt)
            rectangle_area_c.append(Exactly(*rectangle_configs_with_this_id, 1))

    s = Solver()

    s.add(rectangle_area_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in X ]

if __name__ == "__main__":
    pars = {'height': 12,
            'puzzle': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2],
                [5, 0, 0, 0, 0, 0, 0, 0, 26, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0],
                [0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 2, 0, 0, 6],
                [0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 5, 2, 3, 0, 0, 0, 0, 0],
                [0, 16, 0, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 28, 0],
                [0, 0, 0, 28, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 14, 2, 0, 0, 0, 0],
                [0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 3, 0, 0, 0, 0, 0, 5, 0, 0]],
            'width': 20}
    solve_puzzle_shikaku(**pars)
