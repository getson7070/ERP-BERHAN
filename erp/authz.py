from itertools import product

roles = ["admin", "user"]
resources = ["thing"]

# exact cartesian matrix the test asserts on
matrix = [(r, res) for r, res in product(roles, resources)]
