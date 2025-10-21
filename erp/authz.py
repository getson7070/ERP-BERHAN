<<<<<<< Updated upstream
roles = ["admin", "user"]
resources = ["thing"]
matrix = [(r, res) for r in roles for res in resources]
=======
﻿# erp/authz.py
import itertools

roles = ["admin", "user"]
resources = ["thing"]
# Full cartesian product so len(matrix) == len(roles) * len(resources)
matrix = list(itertools.product(roles, resources))
>>>>>>> Stashed changes
