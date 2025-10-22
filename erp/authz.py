roles = ["admin", "user"]
resources = ["thing"]
matrix = [(r, res) for r in roles for res in resources]