import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import DeltaStore, get_store
from jobs.seed import seed_delta_rs


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    base = str(tmp_path_factory.mktemp("warehouse"))
    seed_delta_rs(base)
    app.dependency_overrides[get_store] = lambda: DeltaStore(base, refresh_seconds=0)
    yield TestClient(app)
    app.dependency_overrides.clear()
