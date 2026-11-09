import os
from pathlib import Path

import pytest


@pytest.fixture
def raw_data() -> Path:
    raw = Path("data/raw")
    if not (raw / "tracinginsights").exists():
        if os.environ.get("REQUIRE_DATA") == "1":
            pytest.fail("data/raw missing and REQUIRE_DATA=1")
        pytest.skip("data/raw absent: scoring gate NOT run")
    return raw
