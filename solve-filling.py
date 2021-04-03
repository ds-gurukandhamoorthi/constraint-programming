import itertools
from z3 import *

def flatten(list_of_lists):
    return list(itertools.chain(*list_of_lists))

def IntMatrix(prefix, nb_rows, nb_cols):
    res = [[ Int(f'{prefix}_{i}_{j}') for j in range(nb_cols)]
                            for i in range(nb_rows) ]
    return res

def coerce_eq(variabs, vals):
    variabs = list(variabs)
    vals = list(vals)
    assert len(variabs) == len(vals), 'Lengths of the variables and values must be equal for the intended coercing between them'
    return And([ var == v for var, v in zip(variabs, vals) ])

# Exactly(1) -> False, Exactly(0) -> True, Exactly(2) -> False.
# As would PbEq([ (p, 1) for p in [] ], 1)
def Exactly(*args):
    assert len(args) >= 1, 'Non empty list of arguments expected'
    return PbEq([
        (arg, 1) for arg in args[:-1]],
        args[-1])

# direction = up, down, left, right, -1, +1, -1, +1

# index = line, column
def inside_board(index_lc, *, height, width):
    l, c = index_lc
    return (0 <= l < height) and (0 <= c < width)

def neighbours(index_):
    up, down, left, right = (1, 1, 1, 1)
    l, c = index_
    return [(l-up, c),
        (l+down, c),
        (l, c-left),
        (l, c+right)]

def get_block(index_, *, nb_cells, is_valid_cell):
    if nb_cells == 1:
        return {(index_, )}
    if nb_cells >= 2:
        block_minus_1 = get_block(index_, nb_cells = nb_cells-1, is_valid_cell=is_valid_cell)
        res = set()
        for bl in block_minus_1:
            for cell in bl:
                for neigh in neighbours(cell):
                    if neigh not in bl:
                        if is_valid_cell(neigh):
                            res.add(tuple(sorted([neigh, *bl])))
        return res

# for a given enclosure find its fence/frontier for the given distance
def get_fence(*,enclosure):
    area_and_fence = set()
    for cell in enclosure:
        cell_neighbours = neighbours(cell)
        for cell_neighbour in cell_neighbours:
            area_and_fence.add(cell_neighbour)
    return area_and_fence - set(enclosure)

# count_ contiguous squares at index_ (l, c)
def gen_contiguous_constraints_single(index_, count_, *, width, height, board, puzzle):
    at_ = lambda l, c : board[l][c]
    at_puzzle = lambda l, c : puzzle[l][c]
    def is_valid_cell(ind, current_index=index_, height=height, width=width):
        if ind == current_index: # redundant check at_puzzle(ind) == count_
            return True
        if not inside_board(ind, height=height, width=width):
            return False
        # a cell is considered valid neighbour (to spawn) if it is empty
        # or it has the same count_
        return at_puzzle(*ind) == 0 or at_puzzle(*ind) == count_
    possibs = [] # possible configurations given the count_ of contiguous cells in the block
    blocks = get_block(index_, nb_cells=count_, is_valid_cell=is_valid_cell)
    for block in blocks:
        block_vars = [ at_(*ind) for ind in block ]
        # fence can be thought of as completely encircling the block
        fence = get_fence(enclosure=block)
        geom = { 'width': width, 'height': height }
        fence_inside_board = [ ind for ind in fence
                if inside_board(ind, **geom) ]
        fence_var = [ at_(*ind) for ind in fence_inside_board ]
        fenced_enclosure = And(
                coerce_eq(block_vars, [count_] * len(block_vars)),
                And([var != count_ for var in fence_var]))
        possibs.append(simplify(fenced_enclosure))
    return Exactly(*possibs, 1) #only one configuration would prevail

def gen_contiguous_constraints(puzzle, board, *, width, height):
    pars = {'board': board, 'width': width,
            'height': height, 'puzzle': puzzle}
    all_contig_spaces = [ ((i, j), puzzle[i][j])
        for i, j in itertools.product(range(height), range(width))
        if puzzle[i][j] > 0 ]
    constraints = [ gen_contiguous_constraints_single(ind, count_, **pars)
            for ind, count_ in all_contig_spaces ]
    return constraints

def solve_puzzle_range(puzzle, *, height, width):
    board = IntMatrix('b', nb_rows=height, nb_cols=width)
    pars = {'board': board, 'width': width, 'height': height}

    vars_ = flatten(board)
    vals = flatten(puzzle)
    instance_c = [var == val for var, val in zip(vars_, vals)
            if val > 0]
    contig_c = gen_contiguous_constraints(puzzle, **pars)

    # There is no empty cell: And cell values range from 1 to height*width
    complete_c = [ And(0 < cell, cell < height * width + 1)
            for cell in flatten(board) ]

    # The model wants the numbers outside the block to be different than
    # the number (count) in the block. But to resolve this constraint it
    # uses big numbers 32, 211 ... until the max we've put.
    # It doesn't try 1 there.
    # So it exhausts (if we have two 1) 221 * 221 = 48841 possbilities.
    # We want to avoid that by saying Except for 1 all other counts have at least
    # one neighbour that is equal to it.
    # We have dodged the problem by using an optimizer (minimize cost).
    # But it is better to encode and incoroporate this constraint in the model.
    geom = { 'width': width, 'height': height }
    at_ = lambda l, c : board[l][c]
    def valid_neighbours(l, c):
        return [ neigh for neigh in neighbours((l, c))
                if inside_board(neigh, **geom) ]
    def at_least_one_neighbour_is_same(l, c):
        return Or([ at_(l, c) == at_(*neigh)
                for neigh in valid_neighbours(l, c) ])
    ortho_neigh_c = [ Xor(
        board[l][c] == 1,
        at_least_one_neighbour_is_same(l, c))
        for l, c in itertools.product(range(height), range(width)) ]

    # s = Solver()
    # s.add(complete_c + contig_c + instance_c + ortho_neigh_c)
    # s.check()
    # m = s.model()
    # solution_model = [ [ m[cell].as_long() for cell in row] for row in board ]
    # return solution_model

    opt = Optimize()
    opt.add(complete_c + contig_c + instance_c + ortho_neigh_c)
    cost = Int('cost')
    opt.add(cost == Sum(vars_))
    h = opt.minimize(cost)
    opt.check()
    opt.lower(h)
    m = opt.model()
    solution_model = [ [ m[cell].as_long() for cell in row] for row in board ]

    optimizer_check_model = opt
    while True:
        print('checking solution')
        print(solution_model)
        optimizer_check_model.push()
        contig_model_c = gen_contiguous_constraints(solution_model, **pars)
        instance_model_c = [ var == val
                for var, val in zip(vars_, flatten(solution_model))
                if val > 0]
        # check that the numbers in the solution verifies the
        # contiguouness constraint
        optimizer_check_model.add(contig_model_c)
        optimizer_check_model.add(instance_model_c) # redundant?
        if optimizer_check_model.check() == sat:
                return solution_model #HERE IS THE RETURN STATEMENT
        print('rejecting solution')
        print(solution_model)

        optimizer_check_model.pop()
        # the rejected solution is added after 'pop'. This is how it is
        # added to the model
        optimizer_check_model.add(Not(And(instance_model_c)))
        optimizer_check_model.check()
        optimizer_check_model.lower(h)
        m = optimizer_check_model.model()
        solution_model = [ [ m[cell].as_long() for cell in row ] for row in board ]

if __name__ == "__main__":
    puzzle_h9_w13 = [
            [0, 2, 0, 0, 3, 0, 4, 0, 3, 0, 0, 0, 6],
            [0, 0, 0, 5, 3, 0, 0, 0, 0, 0, 0, 0, 2],
            [0, 3, 0, 2, 6, 2, 2, 0, 2, 4, 4, 0, 0],
            [0, 6, 5, 0, 0, 0, 0, 0, 0, 0, 0, 4, 3],
            [0, 0, 3, 0, 4, 0, 6, 0, 2, 2, 0, 0, 2],
            [0, 4, 0, 0, 4, 0, 0, 0, 0, 8, 0, 0, 7],
            [0, 0, 0, 0, 0, 2, 0, 4, 0, 0, 7, 7, 7],
            [3, 2, 0, 0, 0, 2, 0, 2, 3, 0, 5, 4, 0],
            [9, 0, 0, 0, 0, 0, 4, 0, 0, 3, 0, 0, 0]]

    width, height= 13, 9 # a.k.a nb_columns, nb_rows

    solve_puzzle_range(puzzle_h9_w13, height=height, width=width)

    puzzle_h13_w17 = [
            [5, 3, 0, 0, 0, 0, 5, 0, 5, 0, 0, 7, 0, 5, 0, 0, 0],
            [0, 0, 0, 5, 0, 9, 5, 5, 0, 0, 6, 0, 0, 0, 5, 3, 4],
            [2, 0, 0, 0, 0, 0, 0, 3, 6, 6, 0, 0, 0, 0, 0, 6, 0],
            [9, 0, 4, 0, 3, 0, 9, 0, 0, 6, 6, 0, 0, 4, 6, 6, 0],
            [0, 0, 0, 3, 0, 0, 2, 3, 0, 0, 0, 0, 3, 4, 0, 0, 6],
            [0, 0, 0, 5, 0, 0, 0, 5, 0, 8, 4, 0, 0, 5, 0, 4, 3],
            [0, 9, 0, 3, 0, 0, 0, 0, 8, 0, 5, 0, 3, 0, 0, 3, 0],
            [0, 7, 2, 9, 0, 9, 7, 0, 8, 0, 0, 0, 2, 2, 0, 0, 0],
            [7, 0, 0, 7, 9, 9, 0, 4, 8, 0, 5, 0, 0, 0, 2, 0, 0],
            [0, 0, 3, 9, 0, 9, 0, 7, 0, 2, 8, 0, 0, 8, 6, 6, 6],
            [4, 0, 0, 0, 0, 0, 0, 3, 0, 2, 0, 8, 0, 0, 0, 0, 0],
            [5, 0, 3, 0, 0, 0, 3, 5, 0, 0, 3, 2, 6, 6, 9, 0, 0],
            [0, 0, 0, 0, 0, 0, 4, 0, 0, 3, 0, 0, 0, 6, 9, 0, 0]]

    width, height= 17, 13 # a.k.a nb_columns, nb_rows

    solve_puzzle_range(puzzle_h13_w17, height=height, width=width)
