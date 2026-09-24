# tests/test_cursos.py
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Incorporar la carpeta API al path de importación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "API")))

from main import app
from database import inicializar_base_datos

# Inicializar estado de base de datos para pruebas
inicializar_base_datos()
client = TestClient(app)

def test_endpoint_raiz():
    """Valida disponibilidad del servicio."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["estado"] == "Operativo"

def test_happy_path_docente_con_carga():
    """CA-01: Docente existente con cursos asignados (ID 1 - Diego Rubilar)."""
    response = client.get("/api/cursos?docente_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["tiene_carga"] is True
    assert data["total_cursos"] >= 1
    assert any(c["nombre"] == "3° Medio A" for c in data["cursos"])

def test_regla_negocio_docente_sin_carga():
    """CA-03: Docente registrado sin asignación académica (ID 4 - Ignacio Pino)."""
    response = client.get("/api/cursos?docente_id=4")
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["tiene_carga"] is False
    assert data["total_cursos"] == 0
    assert "Contacte a U.T.P." in data["mensaje"]

def test_excepcion_docente_inexistente():
    """Manejo de error: Identificador no registrado en SQLite."""
    response = client.get("/api/cursos?docente_id=999")
    assert response.status_code == 404
    assert "no se encuentra registrado" in response.json()["detail"]

def test_validacion_parametro_invalido():
    """CA-02: Validación Pydantic para docente_id < 1."""
    response = client.get("/api/cursos?docente_id=0")
    assert response.status_code == 422