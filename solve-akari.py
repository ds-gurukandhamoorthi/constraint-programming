from z3 import *
import itertools
from more_z3 import IntMatrix, Exactly, coerce_eq
from puzzles_common import flatten, transpose, inside_board
from funcy import isnone
from more_itertools import split_when
from funcy import walk_keys, walk_values
from funcy import partial, compose
from puzzles_common import ortho_neighbours as neighbours

LIGHT_BULB, NOT_LIGHT_BULB = 1, 0
WALL = -1

def get_indices_contiguous_elems_verifying(iterable, pred):
    indices_satisfying_pred = [ i for i, elem in enumerate(iterable) if pred(elem) ]
    # we mean 'not successive'. here this is sufficient. otherwise y != x + 1 or x != y + 1
    not_contiguous = lambda x, y: y != x + 1
    indices_grouped_by_contiguity = split_when(indices_satisfying_pred, not_contiguous)
    return list(indices_grouped_by_contiguity)

# "cages" as in 'killer sudoku'.  Here any contiguous empty cells.
def get_horizontal_cages_single_row(row, row_index):
    is_empty_cell = isnone
    cages = get_indices_contiguous_elems_verifying(row, is_empty_cell)
    add_row_index = lambda lst: [(row_index, elem) for elem in lst]
    res = dict()
    for cage in cages:
        for x in cage:
            res[(row_index, x)] = add_row_index(cage)
    return res

def get_horizontal_cages(rows):
    res = dict()
    for i, row in enumerate(rows):
        res = {**res, **get_horizontal_cages_single_row(row, i)}
    return res

def get_vertical_cages(rows):
    transpose_coordinates = lambda t: (t[1], t[0])
    res = get_horizontal_cages(transpose(rows))
    res = walk_keys(transpose_coordinates, res)
    transpose_coordinates_lst = compose(list, partial(map, transpose_coordinates))
    res = walk_values(transpose_coordinates_lst, res)
    return res

def solve_akari(puzzle, *, height, width):
    X = IntMatrix('n', nb_rows=height, nb_cols=width)

    cell_vars = flatten(X)
    clues = flatten(puzzle)
    assert len(cell_vars) == len(clues), "Discrepancy between puzzle and cell-variables"

    complete_c = []
    for cell_var, clue in zip(cell_vars, clues):
        if clue == WALL or clue in (0,1,2,3,4):
            complete_c.append(cell_var == WALL)
        else:
            complete_c.append(Xor(cell_var == LIGHT_BULB, cell_var == NOT_LIGHT_BULB))

    geom = {'width': width, 'height': height}
    at_ = lambda l, c: X[l][c]

    def valid_neighbours(l, c):
        return [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, **geom) ]

    def gen_count_lightbulb_constraint(l, c, count_lightbulbs):
        neigh_as_light_bulb =  [at_(*cell) == LIGHT_BULB for cell in valid_neighbours(l, c)]
        return Exactly(*neigh_as_light_bulb, count_lightbulbs)

    count_surrounding_light_bulbs_c =[]
    for l, c in itertools.product(range(height), range(width)):
        clue = puzzle[l][c]
        if clue in (0, 1, 2, 3, 4):
            cnstr = gen_count_lightbulb_constraint(l, c, count_lightbulbs=clue)
            count_surrounding_light_bulbs_c.append(cnstr)

    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    # think of this as vectorialization of 'value'
    def vars_eq_scalar(variabs, value):
        return [var == value for var in variabs]

    horizontal_cages_indexed = get_horizontal_cages(puzzle)
    vertical_cages_indexed = get_vertical_cages(puzzle)


    horizontal_cages = set(tuple(sorted(cage)) for cage in horizontal_cages_indexed.values())
    vertical_cages = set(tuple(sorted(cage)) for cage in vertical_cages_indexed.values())

    # two lightbulbs can't illuminate each other. territory? forbid encroachment?

    # there can be at most one bulb in each horizontal cage
    _h_no_encroachment_c = []
    for hcage in horizontal_cages:
        light_bulbs_in_cage = vars_eq_scalar(get_vars_at(hcage), LIGHT_BULB)
        cnstrnt = AtMost(*light_bulbs_in_cage, 1)
        _h_no_encroachment_c.append(cnstrnt)


    _v_no_encroachment_c = []
    for vcage in vertical_cages:
        light_bulbs_in_cage = vars_eq_scalar(get_vars_at(vcage), LIGHT_BULB)
        cnstrnt = AtMost(*light_bulbs_in_cage, 1)
        _v_no_encroachment_c.append(cnstrnt)

    no_encroachment_c = _h_no_encroachment_c + _v_no_encroachment_c

    assert sorted(tuple(vertical_cages_indexed.keys())) == sorted(tuple(horizontal_cages_indexed.keys())), "verical cages and horizontal cages must have same keys"

    all_empty_cells_illuminated_c = []
    for coord in vertical_cages_indexed.keys():
        vcage = vertical_cages_indexed[coord]
        hcage = horizontal_cages_indexed[coord]
        horiz_cage_has_lightbulb = Exactly(*vars_eq_scalar(get_vars_at(hcage), LIGHT_BULB), 1)
        vertic_cage_has_lightbulb = Exactly(*vars_eq_scalar(get_vars_at(vcage), LIGHT_BULB), 1)
        cnstrnt = Or(horiz_cage_has_lightbulb, vertic_cage_has_lightbulb)
        all_empty_cells_illuminated_c.append(cnstrnt)



    s = Solver()
    s.add(complete_c + count_surrounding_light_bulbs_c + no_encroachment_c + all_empty_cells_illuminated_c)

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in X]


if __name__ == "__main__":
    pars = {'height': 10,
            'puzzle': [[-1, None, 1, None, None, 0, None, None, -1, None, None, None, -1, None, None, None, -1, None, 0, -1],
                [None, None, None, None, None, None, None, None, None, 0, None, None, None, None, -1, None, 0, None, None, -1],
                [1, None, 0, None, 1, None, None, None, None, None, None, 1, -1, None, 2, None, None, None, None, None],
                [None, None, 0, None, 2, None, 1, None, None, None, 1, None, None, None, None, None, None, None, -1, None],
                [None, None, -1, None, None, -1, None, None, -1, 1, -1, None, -1, None, None, -1, None, None, -1, -1],
                [None, -1, None, None, None, None, None, None, None, None, None, None, None, -1, -1, None, None, -1, -1, -1],
                [2, None, None, None, -1, None, None, -1, None, None, 0, -1, 1, None, None, None, None, None, 2, None],
                [None, None, None, None, -1, 1, None, None, None, None, None, None, None, -1, -1, None, None, -1, -1, None],
                [None, None, 1, None, None, None, None, None, None, None, None, None, -1, None, None, 3, None, None, None, None],
                [-1, None, None, None, 2, None, None, -1, None, None, None, 2, None, None, None, -1, None, None, -1, None]],
            'width': 20}

    solve_akari(**pars)
