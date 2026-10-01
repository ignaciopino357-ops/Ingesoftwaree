# API/database.py
# Base de datos SQLite (incluida en Python, no requiere instalar nada).

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Se puede cambiar con la variable de entorno ALERTA_DB_PATH (los tests la usan
# para no tocar la base real).
DB_NAME = os.environ.get("ALERTA_DB_PATH") or str(Path(__file__).resolve().parent / "sprint1.db")

PASSWORD_INICIAL = "123456"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS Usuario (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK (rol IN
                    ('DOCENTE','PROFESOR_JEFE','CONVIVENCIA_ESCOLAR','UTP','DIRECTIVO')),
    activo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Curso (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre            TEXT NOT NULL,
    nivel             TEXT NOT NULL,
    letra             TEXT NOT NULL,
    anio_lectivo      INTEGER NOT NULL,
    id_profesor_jefe  INTEGER REFERENCES Usuario(id),
    total_estudiantes INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Estudiante (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rut                 TEXT NOT NULL UNIQUE,
    nombres             TEXT NOT NULL,
    apellidos           TEXT NOT NULL,
    email               TEXT NOT NULL UNIQUE,
    password_hash       TEXT NOT NULL,
    id_curso            INTEGER NOT NULL REFERENCES Curso(id),
    nivel_riesgo_actual TEXT NOT NULL DEFAULT 'BAJO'
                        CHECK (nivel_riesgo_actual IN ('BAJO','MEDIO','ALTO'))
);

CREATE TABLE IF NOT EXISTS Asignatura (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL UNIQUE
);

-- Cada fila es una nota puntual. id_asignatura NULL = registro general (carga masiva)
CREATE TABLE IF NOT EXISTS RegistroAcademico (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante  INTEGER NOT NULL REFERENCES Estudiante(id),
    id_asignatura  INTEGER REFERENCES Asignatura(id),
    fecha          TEXT NOT NULL,
    asistencia     REAL,
    nota           REAL
);

CREATE TABLE IF NOT EXISTS CasoIntervencion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante   INTEGER NOT NULL REFERENCES Estudiante(id),
    motivo          TEXT NOT NULL CHECK (motivo IN
                    ('ACADEMICO','ASISTENCIA','CONDUCTUAL','SOCIOEMOCIONAL')),
    estado          TEXT NOT NULL DEFAULT 'PENDIENTE'
                    CHECK (estado IN ('PENDIENTE','EN_PROCESO','RESUELTA')),
    observaciones   TEXT,
    fecha_creacion  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# Evita registros duplicados (mismo alumno + asignatura + fecha). Se crea después de limpiar duplicados.
INDICE_UNICO_REGISTRO = """
CREATE UNIQUE INDEX IF NOT EXISTS ux_registro_unico
ON RegistroAcademico (id_estudiante, COALESCE(id_asignatura, 0), fecha)
"""

ASIGNATURAS = ["Matemáticas", "Lenguaje", "Historia", "Ciencias Naturales",
               "Educación Física", "Inglés", "Música", "Artes Visuales"]


# ---------------------------------------------------------------- contraseñas
_ITERACIONES = 200_000


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 con sal aleatoria. Formato: pbkdf2_sha256$iter$sal$hash"""
    sal = secrets.token_hex(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(sal), _ITERACIONES)
    return f"pbkdf2_sha256${_ITERACIONES}${sal}${derivado.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    """Verifica contra el formato nuevo y también contra SHA-256 simple (BD antiguas)."""
    if almacenado.startswith("pbkdf2_sha256$"):
        try:
            _, iteraciones, sal, esperado = almacenado.split("$")
            derivado = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(sal), int(iteraciones)
            ).hex()
        except ValueError:
            return False
        return hmac.compare_digest(derivado, esperado)
    antiguo = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(antiguo, almacenado)


# ------------------------------------------------------------------ conexión
def obtener_conexion():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


@contextmanager
def conexion_bd():
    """Abre una conexión, hace commit si todo sale bien, rollback si falla, y siempre la cierra."""
    con = obtener_conexion()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ---------------------------------------------------------- inicialización
def _esquema_obsoleto(con) -> bool:
    """True si existe una BD de una versión anterior (sin la columna email)."""
    for tabla in ("Usuario", "Estudiante"):
        columnas = {f[1] for f in con.execute(f"PRAGMA table_info({tabla})").fetchall()}
        if columnas and "email" not in columnas:
            return True
    return False


def inicializar_base_datos():
    con = obtener_conexion()
    if _esquema_obsoleto(con):
        print(f"[database] Esquema antiguo detectado: se reconstruye {DB_NAME}")
        con.close()
        Path(DB_NAME).unlink(missing_ok=True)
        con = obtener_conexion()

    try:
        con.executescript(ESQUEMA)

        # Limpia duplicados previos (deja el más reciente) y luego protege con índice único
        con.execute(
            """DELETE FROM RegistroAcademico WHERE id NOT IN (
                   SELECT MAX(id) FROM RegistroAcademico
                   GROUP BY id_estudiante, COALESCE(id_asignatura, 0), fecha)"""
        )
        con.execute(INDICE_UNICO_REGISTRO)
        con.commit()

        if con.execute("SELECT COUNT(*) FROM Usuario").fetchone()[0] == 0:
            _cargar_datos_demo(con)

        # total_estudiantes siempre coherente con los alumnos reales
        con.execute(
            "UPDATE Curso SET total_estudiantes = "
            "(SELECT COUNT(*) FROM Estudiante e WHERE e.id_curso = Curso.id)"
        )
        con.commit()
    finally:
        con.close()


def _cargar_datos_demo(con):
    hash_demo = hash_password(PASSWORD_INICIAL)  # todos los usuarios de prueba: "123456"

    con.executemany(
        "INSERT INTO Usuario (id, nombre_completo, email, password_hash, rol) VALUES (?,?,?,?,?)",
        [
            (1, "Diego Rubilar", "diego.docente@liceo.cl", hash_demo, "DOCENTE"),
            (2, "Mirko Massa", "mirko.jefe@liceo.cl", hash_demo, "PROFESOR_JEFE"),
            (3, "Constanza Rodriguez", "coni.convivencia@liceo.cl", hash_demo, "CONVIVENCIA_ESCOLAR"),
            (4, "Ignacio Pino", "ignacio.utp@liceo.cl", hash_demo, "UTP"),
            (5, "María Pérez", "maria.directivo@liceo.cl", hash_demo, "DIRECTIVO"),
        ],
    )

    con.executemany(
        "INSERT INTO Curso (id, nombre, nivel, letra, anio_lectivo, id_profesor_jefe) VALUES (?,?,?,?,?,?)",
        [
            (101, "1° Medio A", "Enseñanza Media", "A", 2026, 2),
            (102, "2° Medio B", "Enseñanza Media", "B", 2026, 2),
            (103, "3° Medio A", "Enseñanza Media", "A", 2026, 1),
            (104, "4° Medio A", "Enseñanza Media", "A", 2026, 1),
            (105, "2° Medio A", "Enseñanza Media", "A", 2026, 2),
            (106, "1° Medio A", "Enseñanza Media", "A", 2026, 2),
            (107, "1° Medio B", "Enseñanza Media", "B", 2026, 2),
            (108, "1° Medio C", "Enseñanza Media", "C", 2026, 2),
        ],
    )

    con.executemany(
        "INSERT INTO Asignatura (id, nombre) VALUES (?,?)",
        list(enumerate(ASIGNATURAS, start=1)),
    )

    con.executemany(
        "INSERT INTO Estudiante (id, rut, nombres, apellidos, email, password_hash, id_curso, nivel_riesgo_actual)"
        " VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, "20.111.222-3", "Ana", "Soto Pérez", "ana.soto@alumno.liceo.cl", hash_demo, 101, "BAJO"),
            (2, "19.333.444-5", "Luis", "Rojas Muñoz", "luis.rojas@alumno.liceo.cl", hash_demo, 102, "ALTO"),
            (3, "21.555.666-7", "Sofía", "Vega Contreras", "sofia.vega@alumno.liceo.cl", hash_demo, 103, "MEDIO"),
            (4, "22.777.888-9", "Tomás", "Fuentes Díaz", "tomas.fuentes@alumno.liceo.cl", hash_demo, 104, "ALTO"),
            (5, "23.999.000-1", "Isabel", "Cárdenas Rojas", "isabel.cardenas@alumno.liceo.cl", hash_demo, 105, "BAJO"),
            (6, "24.111.222-3", "Miguel", "Gómez Fuentes", "miguel.gomez@alumno.liceo.cl", hash_demo, 105, "MEDIO"),
        ],
    )

    # 4 notas por asignatura para los 3 primeros alumnos (coherentes con su nivel de riesgo)
    patrones = {
        1: [6.5, 6.2, 6.8, 6.0],   # Ana: BAJO -> notas altas
        2: [3.5, 4.0, 3.2, 3.8],   # Luis: ALTO -> notas bajas
        3: [5.0, 5.5, 4.8, 5.2],   # Sofía: MEDIO -> notas intermedias
    }
    asistencias = {1: 96, 2: 74, 3: 85}
    fechas = ["2026-04-15", "2026-05-15", "2026-06-15", "2026-07-15"]

    registros = []
    for id_est, notas in patrones.items():
        for id_asig in range(1, len(ASIGNATURAS) + 1):
            variacion = ((id_asig % 3) - 1) * 0.2  # pequeña variación por asignatura
            for i, fecha in enumerate(fechas):
                nota = round(min(7.0, max(1.0, notas[i] + variacion)), 1)
                registros.append((id_est, id_asig, fecha, asistencias[id_est], nota))

    con.executemany(
        "INSERT INTO RegistroAcademico (id_estudiante, id_asignatura, fecha, asistencia, nota) VALUES (?,?,?,?,?)",
        registros,
    )
    con.commit()
