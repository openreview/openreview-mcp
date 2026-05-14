import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def best_practices_path():
    return os.path.join(FIXTURES_DIR, "best_practices.md")
