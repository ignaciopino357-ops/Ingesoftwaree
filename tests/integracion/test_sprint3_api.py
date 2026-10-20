"""Criterios del Sprint 3 a través de la API REST (JWT + RBAC)."""
from tests.conftest import token

CURSO_A, EMILIA = 1, 9


def test_alumno_obtiene_solo_sus_datos(cliente):
    r = cliente.get("/api/alumno/mis-datos", headers=token(cliente, "alumno3", "alumno123"))
    assert r.status_code == 200
    datos = r.json()
    assert datos["curso"] == "3° Medio A" and datos["asignaturas"][0]["nombre"] == "Lenguaje"
    assert "2026-10-02" in datos["ausencias"]
    assert "riesgo" not in r.text


def test_mis_datos_es_solo_para_alumnos(cliente):
    assert cliente.get("/api/alumno/mis-datos", headers=token(cliente, "pjara", "profe123")).status_code == 403
    assert cliente.get("/api/alumno/mis-datos").status_code == 401


def test_alertas_y_marcar_revisada(cliente):
    cabecera = token(cliente, "pjara", "profe123")
    alertas = cliente.get("/api/alertas", headers=cabecera).json()
    assert {a["tipo"] for a in alertas} == {"riesgo_alto", "ausencias"}
    primera = alertas[0]["id"]
    assert cliente.post(f"/api/alertas/{primera}/revisada", headers=cabecera).status_code == 200
    assert len(cliente.get("/api/alertas", headers=cabecera).json()) == 1


def test_alerta_ajena_da_403_e_inexistente_404(cliente):
    cabecera = token(cliente, "cmunoz", "profe123")
    assert cliente.get("/api/alertas", headers=cabecera).json() == []
    assert cliente.post("/api/alertas/1/revisada", headers=cabecera).status_code == 403
    assert cliente.post("/api/alertas/999/revisada", headers=cabecera).status_code == 404


def test_historial_por_semana(cliente):
    cabecera = token(cliente, "pjara", "profe123")
    semanas = cliente.get(f"/api/cursos/{CURSO_A}/alumnos/{EMILIA}/historial", headers=cabecera).json()
    assert semanas[0]["lunes"] == "2026-07-27" and semanas[0]["riesgo"] == "Sin datos"
    assert any(s["riesgo"] == "Alto" for s in semanas)
    otro = token(cliente, "cmunoz", "profe123")
    assert cliente.get(f"/api/cursos/{CURSO_A}/alumnos/{EMILIA}/historial", headers=otro).status_code == 403


def test_filtrar_riesgo_del_curso_por_estado(cliente):
    cabecera = token(cliente, "pjara", "profe123")
    r = cliente.get(f"/api/cursos/{CURSO_A}/riesgo?estado=Alto&estado=Sin datos", headers=cabecera).json()
    assert {a["riesgo"] for a in r["alumnos"]} == {"Alto", "Sin datos"}
    assert sum(r["conteo"].values()) == 8               # el conteo sigue siendo del curso completo
    assert cliente.get(f"/api/cursos/{CURSO_A}/riesgo?estado=Rojo", headers=cabecera).status_code == 422


def test_resumen_para_directiva_sin_nombres(cliente):
    r = cliente.get("/api/riesgo/resumen", headers=token(cliente, "directiva", "directiva123"))
    assert r.status_code == 200 and r.json()["total"]["Alto"] == 1
    assert "Emilia" not in r.text
    assert cliente.get("/api/riesgo/resumen", headers=token(cliente, "pjara", "profe123")).status_code == 403


def test_registrar_usuario_por_api(cliente):
    cabecera = token(cliente, "directiva", "directiva123")
    nuevo = {"nombre": "Nora Paz", "usuario": "npaz", "clave": "secreto1", "rol": "alumno"}
    r = cliente.post("/api/usuarios", json=nuevo, headers=cabecera)
    assert r.status_code == 201 and r.json()["rol"] == "alumno"
    assert cliente.post("/api/usuarios", json=nuevo, headers=cabecera).status_code == 409
    corta = cliente.post("/api/usuarios", json={**nuevo, "usuario": "otra", "clave": "123"}, headers=cabecera)
    assert corta.status_code == 400 and "clave" in corta.json()["errores"]
    assert cliente.post("/api/login", json={"usuario": "npaz", "clave": "secreto1"}).status_code == 200
    alumnos = cliente.get("/api/usuarios?rol=alumno", headers=cabecera).json()
    assert "npaz" in {a["usuario"] for a in alumnos}


def test_solo_directiva_registra_por_api(cliente):
    r = cliente.post("/api/usuarios", json={"nombre": "X", "usuario": "xxx", "clave": "secreto1", "rol": "alumno"},
                     headers=token(cliente, "pjara", "profe123"))
    assert r.status_code == 403
