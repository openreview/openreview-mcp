import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def llm_txt_path():
    return os.path.join(FIXTURES_DIR, "llm.txt")


@pytest.fixture
def examples_md_path():
    return os.path.join(FIXTURES_DIR, "examples.md")
