from z3 import And, PbEq, Int, Bool
import operator

def coerce_comp_op(variabs, vals, comparison_op):
    variabs = list(variabs)
    vals = list(vals)
    assert len(variabs) == len(vals), 'Lengths of the variables and values must be equal for the intended coercing between them'
    return And( *map(comparison_op, variabs, vals) )


def coerce_eq(variabs, vals):
    return coerce_comp_op(variabs, vals, operator.eq) # all(variab == val)

def coerce_ge(variabs, vals):
    return coerce_comp_op(variabs, vals, operator.ge) # all(variab >= val)

def coerce_le(variabs, vals):
    return coerce_comp_op(variabs, vals, operator.le) # all(variab <= val)

def IntMatrix(prefix, nb_rows, nb_cols):
    res = [[ Int(f'{prefix}_{i}_{j}') for j in range(nb_cols)]
                            for i in range(nb_rows) ]
    return res

def BoolMatrix(prefix, nb_rows, nb_cols):
    res = [[ Bool(f'{prefix}_{i}_{j}') for j in range(nb_cols)]
                            for i in range(nb_rows) ]
    return res

# Exactly(1) -> False, Exactly(0) -> True, Exactly(2) -> False.
# As would PbEq([ (p, 1) for p in [] ], 1)
def Exactly(*args):
    assert len(args) >= 1, 'Non empty list of arguments expected'
    return PbEq([
        (arg, 1) for arg in args[:-1]],
        args[-1])
