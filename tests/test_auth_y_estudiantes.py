# tests/test_auth_y_estudiantes.py
import io


def test_login_docente(client):
    r = client.post("/api/login", json={"email": "diego.docente@liceo.cl", "password": "123456"})
    assert r.status_code == 200
    assert r.json()["tipo"] == "DOCENTE"


def test_login_estudiante(client):
    r = client.post("/api/login", json={"email": "ana.soto@alumno.liceo.cl", "password": "123456"})
    assert r.status_code == 200
    assert r.json()["tipo"] == "ESTUDIANTE"


def test_login_incorrecto(client):
    r = client.post("/api/login", json={"email": "ana.soto@alumno.liceo.cl", "password": "mala"})
    assert r.status_code == 401
    r2 = client.post("/api/login", json={"email": "nadie@x.cl", "password": "123456"})
    assert r2.status_code == 401
    assert r.json()["detail"] == r2.json()["detail"]  # no revela si el correo existe


def test_portal_estudiante_agrupa_por_asignatura(client):
    d = client.get("/api/estudiantes/1").json()
    assert d["promedio_general"] is not None
    assert "Matemáticas" in d["asignaturas"]
    assert len(d["asignaturas"]["Matemáticas"]["notas"]) == 4


def test_lista_de_curso_no_expone_password_hash(client):
    d = client.get("/api/cursos/101/estudiantes").json()
    assert d["estudiantes"]
    assert all("password_hash" not in e for e in d["estudiantes"])


def test_crear_estudiante_y_duplicado(client):
    cuerpo = {"rut": "25.000.111-2", "nombres": "Nuevo", "apellidos": "Alumno",
              "email": "nuevo.alumno@alumno.liceo.cl", "id_curso": 101}
    r = client.post("/api/estudiantes", json=cuerpo)
    assert r.status_code == 201
    assert client.post("/api/estudiantes", json=cuerpo).status_code == 409
    assert client.post("/api/login", json={"email": cuerpo["email"], "password": "123456"}).status_code == 200


def test_crear_estudiante_curso_inexistente(client):
    cuerpo = {"rut": "26.000.111-2", "nombres": "Otro", "apellidos": "Alumno",
              "email": "otro@alumno.liceo.cl", "id_curso": 9999}
    assert client.post("/api/estudiantes", json=cuerpo).status_code == 404


def test_carga_csv_valida_y_con_errores(client):
    csv_ = "id_estudiante,fecha,nota,asistencia\n1,2026-08-15,6.5,95\n1,2026-09-15,9.9,95\n2,2026-08-15,5,80\n"
    r = client.post("/api/cursos/101/cargar-notas",
                    files={"archivo": ("notas.csv", io.BytesIO(csv_.encode()), "text/csv")})
    assert r.status_code == 200
    d = r.json()
    assert d["filas_insertadas"] == 1          # solo la fila 2 (alumno 1, nota válida)
    assert d["filas_con_error"] == 2           # nota 9.9 fuera de rango + alumno 2 es de otro curso
    assert {e["fila"] for e in d["errores"]} == {3, 4}


def test_carga_rechaza_extension_y_curso_inexistente(client):
    r = client.post("/api/cursos/101/cargar-notas",
                    files={"archivo": ("notas.txt", io.BytesIO(b"x"), "text/plain")})
    assert r.status_code == 422
    r = client.post("/api/cursos/9999/cargar-notas",
                    files={"archivo": ("n.csv", io.BytesIO(b"id_estudiante,fecha,nota,asistencia\n"), "text/csv")})
    assert r.status_code == 404


def test_estadisticas_y_exportacion(client):
    assert client.get("/api/cursos/101/estadisticas").status_code == 200
    assert client.get("/api/cursos/9999/estadisticas").status_code == 404
    assert client.get("/api/cursos/101/exportar?formato=xlsx").status_code == 200
    assert client.get("/api/cursos/101/exportar?formato=csv").status_code == 200
    assert client.get("/api/cursos/101/exportar?formato=pdf").status_code == 422
