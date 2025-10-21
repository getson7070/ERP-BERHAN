roles = ["admin", "user"]
resources = ["thing"]
# matrix must be cartesian to satisfy test: len(roles) * len(resources) == len(matrix)
matrix = [(r, res) for r in roles for res in resources]
