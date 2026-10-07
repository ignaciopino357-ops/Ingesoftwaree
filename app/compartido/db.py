"""Base de datos SQLite: conexión, creación de tablas y datos de prueba.

Se usa sqlite3 (incluido en Python) para no agregar dependencias.
La ruta del archivo se puede cambiar con la variable de entorno LICEO_DB.
"""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("LICEO_DB", "liceo.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('directiva', 'profesor', 'alumno'))
);

CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    profesor_id INTEGER REFERENCES usuarios(id)
);

-- Un alumno pertenece a un solo curso (HU-02)
CREATE TABLE IF NOT EXISTS alumnos_curso (
    alumno_id INTEGER PRIMARY KEY REFERENCES usuarios(id),
    curso_id INTEGER NOT NULL REFERENCES cursos(id)
);

CREATE TABLE IF NOT EXISTS asignaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- HU-05: una nota por alumno, asignatura y número de evaluación (1 a 6)
CREATE TABLE IF NOT EXISTS notas (
    alumno_id INTEGER NOT NULL REFERENCES usuarios(id),
    asignatura_id INTEGER NOT NULL REFERENCES asignaturas(id),
    numero INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 6),
    nota REAL NOT NULL CHECK (nota BETWEEN 1.0 AND 7.0),
    PRIMARY KEY (alumno_id, asignatura_id, numero)
);

-- HU-06: P = presente, A = ausente, J = justificado
CREATE TABLE IF NOT EXISTS asistencia (
    alumno_id INTEGER NOT NULL REFERENCES usuarios(id),
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('P', 'A', 'J')),
    PRIMARY KEY (alumno_id, fecha)
);

-- HU-03: un solo semestre activo (id = 1) y la lista de feriados
CREATE TABLE IF NOT EXISTS semestre (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feriados (
    fecha TEXT PRIMARY KEY,
    nombre TEXT NOT NULL
);
"""


def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def conexion():
    """Abre una conexión, hace commit si todo sale bien y siempre la cierra."""
    conn = conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def crear_tablas() -> None:
    with conexion() as conn:
        conn.executescript(ESQUEMA)


def esta_vacia() -> bool:
    with conexion() as conn:
        return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0


def iniciar() -> None:
    """Se llama al arrancar la app: crea tablas y, si está vacía, carga datos de prueba."""
    crear_tablas()
    if esta_vacia():
        from app.compartido.seed import cargar_datos_de_prueba

        cargar_datos_de_prueba()
