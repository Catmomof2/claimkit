from models.models import detention_amount


def test_detention_standard_case():
    assert detention_amount(5.5, 2.0, 75.0) == 262.50


def test_detention_under_free_time_is_zero():
    assert detention_amount(1.5, 2.0, 75.0) == 0.0


def test_detention_exactly_free_time_is_zero():
    assert detention_amount(2.0, 2.0, 75.0) == 0.0


def test_detention_rounds_to_cents():
    assert detention_amount(3.333, 0.0, 10.0) == 33.33
