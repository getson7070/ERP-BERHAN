roles = ["admin", "user"]
resources = ["thing"]
matrix = [(r, res) for r in roles for res in resources]

def is_allowed(role: str, resource: str) -> bool:
    return (role, resource) in matrix
