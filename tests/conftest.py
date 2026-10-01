# tests/conftest.py
# Los tests usan una base de datos temporal: nunca tocan API/sprint1.db.
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))  # permite `import main` y `import API...` desde la raíz

_directorio = tempfile.mkdtemp(prefix="alerta_tests_")
os.environ["ALERTA_DB_PATH"] = os.path.join(_directorio, "test.db")  # antes de importar API.database

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from API.database import inicializar_base_datos  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    inicializar_base_datos()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
