import os
import tempfile

import pytest

# La base de pruebas va en una carpeta temporal, nunca en liceo.db
_TMP = tempfile.mkdtemp()
os.environ["LICEO_DB"] = os.path.join(_TMP, "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.compartido import db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def cliente():
    """Aplicación completa con una base de datos nueva y los datos de prueba."""
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.iniciar()
    with TestClient(app) as c:
        yield c


def entrar(cliente, usuario, clave):
    """Inicia sesión en las páginas web (cookie de sesión)."""
    return cliente.post("/login", data={"usuario": usuario, "clave": clave}, follow_redirects=False)


def token(cliente, usuario, clave) -> dict:
    """Inicia sesión en la API y devuelve el encabezado Authorization listo para usar."""
    respuesta = cliente.post("/api/login", json={"usuario": usuario, "clave": clave})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}
