import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, transpose

def solve_puzzle_yakuso(puzzle, *, height, width, horizontal_sums):
    board = IntMatrix('n', nb_rows=height, nb_cols=width)

    max_possible_number = height

    range_c = [ And(cell >= 0, cell <= max_possible_number)
            for cell in flatten(board) ]

    def list_contains_n_times_val(lst, n, val):
        return Exactly(*[var == val
            for var in lst], n)

    # row contains number n, n times
    row_n_times_n_c = []
    for row in board:
        possibilities = [
            And(list_contains_n_times_val(row, n, n), #n n times
                list_contains_n_times_val(row, width - n, 0)) # 0 everywhere else (width-n) times zero
            for n in range(1, max_possible_number + 1)]
        cnstrnt = Exactly(*possibilities, 1)
        row_n_times_n_c.append(cnstrnt)

    # whole board contains number n, n times
    whole_n_times_n_c = []
    for n in range(1, max_possible_number + 1):
        cnstrnt = list_contains_n_times_val(flatten(board), n, n)
        whole_n_times_n_c.append(cnstrnt)

    at_ = lambda l, c : board[l][c]
    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(height), range(width))
            if puzzle[l][c] >= 0 ]

    # sums of columns noted horizontally at top or bottom in the puzzle
    sum_c = []
    assert len(horizontal_sums) == width, "Incorrent number of horizontal sums"
    for col, ttl in zip(transpose(board), horizontal_sums):
        if ttl >= 0:
            cnstrnt = Sum(col) == ttl
            sum_c.append(cnstrnt)

    s = Solver()

    s.add( range_c + row_n_times_n_c + whole_n_times_n_c + instance_c + sum_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Yakuso/007.a.htm by author Bertrand Leplay 
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'height': 5,
            'horizontal_sums': [-1, -1, 4, 12, 10, 9],
            'puzzle':
            ( (-1,-1,-1,1,-1,-1),
                (-1,-1,-1,-1,3,-1),
                (-1,0,-1,4,0,-1),
                (-1,-1,-1,-1,-1,-1),
                (5,5,-1,-1,-1,-1)),
            'width': 6}
    solve_puzzle_yakuso(**pars)
