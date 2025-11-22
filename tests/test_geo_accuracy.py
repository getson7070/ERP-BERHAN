from erp.services.geo_utils import haversine_m


def test_haversine_reasonable():
    # Addis Ababa approximate block-to-block distance (~3km)
    distance = haversine_m(9.03, 38.74, 9.05, 38.76)
    assert 2000 < distance < 5000
