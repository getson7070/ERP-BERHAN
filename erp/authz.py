roles = ["admin", "user"]
resources = ["thing"]
# each pair in matrix grants access
matrix = [("admin", "thing"), ("user", "thing")]
