import itertools
from z3 import And, Distinct

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
