"""Regresión de BUG-01 y BUG-02 a través de la API y del portal web (taller semana 13).

Reproduce los casos PI-05 y PI-06: antes de la corrección respondían 201 y 500.
"""
from tests.conftest import entrar, token

ANA, PNUEVO = 5, 4


def test_pi05_api_rechaza_alumno_como_profesor_jefe(cliente):
    cab = token(cliente, "directiva", "directiva123")
    r = cliente.post("/api/cursos", headers=cab, json={"nombre": "4° Medio Z", "profesor_id": ANA})
    assert r.status_code == 400
    assert "rol profesor" in r.json()["detail"]
    assert all(c["nombre"] != "4° Medio Z" for c in cliente.get("/api/cursos", headers=cab).json())
    assert cliente.put("/api/cursos/2/profesor", headers=cab, json={"profesor_id": 6}).status_code == 400


def test_pi06_api_profesor_inexistente_es_404_y_no_500(cliente):
    cab = token(cliente, "directiva", "directiva123")
    r = cliente.post("/api/cursos", headers=cab, json={"nombre": "4° Medio Y", "profesor_id": 999})
    assert r.status_code == 404 and r.json()["detail"] == "El profesor jefe elegido no existe."
    assert cliente.put("/api/cursos/1/profesor", headers=cab, json={"profesor_id": 999}).status_code == 404


def test_pi06_web_profesor_inexistente_muestra_mensaje(cliente):
    entrar(cliente, "directiva", "directiva123")
    r = cliente.post("/directiva/cursos", data={"nombre": "4° Medio X", "profesor_id": "999"}, follow_redirects=True)
    assert r.status_code == 200
    assert "El profesor jefe elegido no existe." in r.text


def test_pi04_regresion_curso_con_profesor_valido(cliente):
    cab = token(cliente, "directiva", "directiva123")
    r = cliente.post("/api/cursos", headers=cab, json={"nombre": "4° Medio A", "profesor_id": PNUEVO})
    assert r.status_code == 201 and r.json()["profesor"] == "Rodrigo Pizarro"
