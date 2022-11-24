import itertools
from z3 import *
from more_z3 import IntMatrix, coerce_eq, Exactly
from puzzles_common import flatten, gen_latin_square_constraints, inside_board

def related_by_operation(var_1, var_2, arith_op):
    result, op = int(arith_op[:-1]), arith_op[-1]
    if op == '+':
        return(var_1 + var_2 == result)
    elif op == '*' or op == 'x':
        return(var_1 * var_2 == result)
    elif op == '-':
        return(Or(var_1 - var_2 == result, var_2 - var_1 == result))
    elif op == '/':
        # As there is no '//' in z3
        return(Or(result * var_1 == var_2, result * var_2 == var_1))
    else:
        print(f' Unknown arithmetic operation {arith_op} ')

def solve_puzzle_mathrax(puzzle, *, order, arithemetic_constraints):
    board = IntMatrix('n', nb_rows=order, nb_cols=order)

    latin_c = gen_latin_square_constraints(board, order)

    at_ = lambda l, c : board[l][c]

    # Squares of 4 cells with a given arithmetic constraint
    def gen_proximity_constraints(l, c, arithemetic_constraint):
        square = [ (l, c), (l, c + 1), # towards right
                (l + 1, c), (l + 1, c + 1) ] # towards bottom and right
        val_cells_in_square = [ cell for cell in square
                if inside_board(cell, height=order, width=order)]
        variables_in_square = [ at_(*cell) for cell in val_cells_in_square ]
        if arithemetic_constraint.lower() == 'o':
            # odd
            cnstrnt = And([ n % 2 == 1 for n in variables_in_square ])
        elif arithemetic_constraint.lower() == 'e':
            # even
            cnstrnt = And([ n % 2 == 0 for n in variables_in_square ])
        else:
            diag_0 = variables_in_square[0], variables_in_square[-1]
            diag_1 = variables_in_square[1], variables_in_square[2]
            cnstrnt = And(
                    related_by_operation(*diag_0, arithemetic_constraint),
                    related_by_operation(*diag_1, arithemetic_constraint))
        return cnstrnt

    # arithmetic constraint
    adjacency_c = [ gen_proximity_constraints(l, c, arith)
        for l, c, arith in arithemetic_constraints ]

    instance_c = [ at_(l, c) == puzzle[l][c]
            for l, c in itertools.product(range(order), range(order))
            if puzzle[l][c] > 0 ]

    s = Solver()

    s.add( latin_c + adjacency_c + instance_c )

    s.check()
    m = s.model()
    return [ [m[cell] for cell in row] for row in board ]

if __name__ == "__main__":
    # The following encoded puzzle is from https://www.janko.at/Raetsel/Mathrax/007.a.htm by author Otto Janko
    # Used here for illustrative purpose only. Not for human consumption. In an encoded form to be processesed by z3.
    pars = {'order': 6,
            'puzzle':
            (   (0,4,2,0,0,0),
                (0,0,0,0,0,0),
                (0,0,0,0,0,0),
                (0,0,0,0,0,0),
                (0,0,0,0,0,0),
                (5,0,0,0,0,2)),
            'arithemetic_constraints': [(0, 0,'12x'), (1, 2, 'o'), (3, 4, '6x'), (4, 0, 'o'), (4, 3, '12x')]
            }
    print(solve_puzzle_mathrax(**pars))
