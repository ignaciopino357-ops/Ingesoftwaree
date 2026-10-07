import os
import tempfile

import pytest

# La base de pruebas va en una carpeta temporal, nunca en liceo.db
_TMP = tempfile.mkdtemp()
os.environ["LICEO_DB"] = os.path.join(_TMP, "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app import db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def cliente():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.iniciar()
    with TestClient(app) as c:
        yield c


def entrar(cliente, usuario, clave):
    return cliente.post("/login", data={"usuario": usuario, "clave": clave}, follow_redirects=False)
