import pytest
from fastapi.testclient import TestClient

from quizhub.db import reset_state
from quizhub.main import create_app


@pytest.fixture()
def app():
    reset_state()
    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_instructor():
    return {"Authorization": "Bearer instructor-key"}


@pytest.fixture()
def auth_student():
    return {"Authorization": "Bearer student-key"}


@pytest.fixture()
def auth_student2():
    return {"Authorization": "Bearer student2-key"}
