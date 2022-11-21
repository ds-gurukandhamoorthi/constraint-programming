import itertools
from z3 import And, Distinct
from collections import defaultdict

#transpose a square matrix
transpose = lambda m: list(zip(*m))

def flatten(list_of_lists):
    return list(itertools.chain(*list_of_lists))

# index = line, column
def inside_board(index_lc, *, height, width):
    l, c = index_lc
    return (0 <= l < height) and (0 <= c < width)


def gen_latin_square_constraints(matrix, order):
    assert len(matrix) == order
    assert len(transpose(matrix)) == order
    numbers = itertools.chain(*matrix)
    range_c = [ And(n >= 1, n <= order) for n in numbers ]

    row_c = [ Distinct(row) for row in matrix ]
    col_c = [ Distinct(row) for row in transpose(matrix) ]

    return range_c + row_c + col_c

# We group by content. all cells containing 0 for example
def get_same_block_indices(matrix):
    res = defaultdict(list)
    for l, row in enumerate(matrix):
        for c, val in enumerate(row):
            res[val].append((l, c))
    return res

# serve first the rows then columns. (whatever their length be)
def rows_and_cols(matrix):
    # serve rows
    yield from matrix
    # serve columns. same as yield from tranpose(matrix)
    yield from zip(*matrix)
