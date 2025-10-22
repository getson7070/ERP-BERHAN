from typing import List, Tuple

roles: List[str] = ["admin", "user"]
resources: List[str] = ["thing"]

matrix: List[Tuple[str, str]] = [(r, res) for r in roles for res in resources]

def is_allowed(role: str, resource: str) -> bool:
    return (role, resource) in matrix
