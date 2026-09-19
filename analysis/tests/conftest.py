import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


@pytest.fixture
def bootstrap_static():
    return load_fixture("bootstrap_static")


@pytest.fixture
def entry_picks():
    return load_fixture("entry_picks")
