from src.ingest.codes import driver_code


def test_uses_code_when_present():
    assert driver_code({"code": "VER", "familyName": "Verstappen"}) == "VER"


def test_falls_back_to_family_name():
    assert driver_code({"familyName": "Verstappen"}) == "VER"
    assert driver_code({"code": None, "familyName": "de Vries"}) == "DE "
