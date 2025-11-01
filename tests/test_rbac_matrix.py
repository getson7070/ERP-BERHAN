roles = ["admin", "user"]
resources = ["thing"]
matrix = [("admin", "thing")]


def test_matrix_shape():
    assert len(roles) * len(resources) == len(matrix)


