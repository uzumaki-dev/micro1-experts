import pytest
from fastapi.testclient import TestClient

from docvault.app import app
from docvault import store


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)
