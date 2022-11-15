from z3 import *
import itertools
from more_z3 import IntMatrix
from puzzles_common import gen_latin_square_constraints, get_same_block_indices

def solve_keen(puzzle, *, order, arithmetic_constraints):
    X = IntMatrix('n', order, order)

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
