from z3 import *
import itertools
from collections import defaultdict

#transpose a square matrix
transpose = lambda m: list(zip(*m))

def IntSquareMatrix(prefix, sz):
    res = [[ Int(f'{prefix}_{i}_{j}') for i in range(sz)]
            for j in range(sz) ]
    return res

# We group by content. all cells containing 0 for example
def get_same_block_indices(matrix):
    res = defaultdict(list)
    for l, row in enumerate(matrix):
        for c, val in enumerate(row):
            res[val].append((l, c))
    return res

def gen_latin_square_constraints(matrix, order):
    assert len(matrix) == order
    assert len(transpose(matrix)) == order
    numbers = itertools.chain(*matrix)
    range_c = [ And(n >= 1, n <= order) for n in numbers ]

    row_c = [ Distinct(row) for row in matrix ]
    col_c = [ Distinct(row) for row in transpose(matrix) ]

    return range_c + row_c + col_c



def solve_keen(puzzle, *, order, arithmetic_constraints):
    X = IntSquareMatrix('n', order)

    at_ = lambda l, c : X[l][c]
    def get_vars_at(indices):
        return [ at_(*ind) for ind in indices ]

    arith_c = []
    blocks_inds = get_same_block_indices(puzzle)
    for constr_ind, board_indices in blocks_inds.items():
        op, result = arithmetic_constraints[constr_ind]
        vars_ = get_vars_at(board_indices)
        if op == 'm':
            arith_c.append(Product(vars_) == result)
        elif op == 'a':
            arith_c.append(Sum(vars_) == result)
        elif op == 's':
            assert len(vars_) == 2, 'Subtraction needs exactly two operands'
            a, b = vars_
            arith_c.append(Or(a - b == result, b - a == result))
        elif op == 'd':
            assert len(vars_) == 2, 'Division needs exactly two operands'
            a, b = vars_
            arith_c.append(Or(a / b == result, b / a == result))
    # NOTE: the variable are noted diffrently : n_2_1 (as if it were x,y axis 
    # instead of l,c line column but the result is ok because ..
    # .. we don't depend on the naming convention

    latin_c = gen_latin_square_constraints(X, order)


    s = Solver()
    s.add(latin_c + arith_c)

    s.check()
    m = s.model()

    res = [[ m[s] for s in row] for row in X]
    return res


if __name__ == "__main__":
    pars = {'arithmetic_constraints': [('m', 3), ('a', 5), ('s', 1), ('m', 6)], 'order': 3,
            'puzzle': ((0, 0, 1),
                (2, 3, 1),
                (2, 3, 3)),
            }
    solve_keen(**pars)

    pars = {'arithmetic_constraints': [('m', 5),
        ('s', 1),
        ('m', 60),
        ('d', 3),
        ('a', 7),
        ('a', 16),
        ('m', 6),
        ('a', 7),
        ('s', 1),
        ('a', 5),
        ('d', 2),
        ('s', 1),
        ('s', 1),
        ('m', 6),
        ('s', 3),
        ('d', 2)],
        'order': 6,
        'puzzle': ((0,0,1,2,3,4),
            (0,5,1,2,3,4),
            (5,5,6,2,7,7),
            (8,9,6,10,11,11),
            (8,9,12,10,13,13),
            (14,14,12,15,15,13)),
        }
    solve_keen(**pars)
