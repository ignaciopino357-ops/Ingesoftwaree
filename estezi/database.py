# API/database.py
# Base de datos SQLite (no requiere instalar nada, viene con Python)

import sqlite3
from pathlib import Path

DB_NAME = str(Path(__file__).resolve().parent / "sprint1.db")

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
    id_curso            INTEGER NOT NULL REFERENCES Curso(id),
    nivel_riesgo_actual TEXT NOT NULL DEFAULT 'BAJO'
                        CHECK (nivel_riesgo_actual IN ('BAJO','MEDIO','ALTO'))
);

CREATE TABLE IF NOT EXISTS RegistroAcademico (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante  INTEGER NOT NULL REFERENCES Estudiante(id),
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

HASH_123456 = "$2a$08$DTaPSyzh0psan5NVVUXIieoFHjbWKwErNo/BNLhax3efuADVLYX6a"


def obtener_conexion():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_base_datos():
    conexion = obtener_conexion()
    conexion.executescript(ESQUEMA)

    if conexion.execute("SELECT COUNT(*) FROM Usuario").fetchone()[0] == 0:
        conexion.executemany(
            "INSERT INTO Usuario (id, nombre_completo, email, password_hash, rol) VALUES (?,?,?,?,?)",
            [
                (1, "Diego Rubilar", "diego.docente@liceo.cl", HASH_123456, "DOCENTE"),
                (2, "Mirko Massa", "mirko.jefe@liceo.cl", HASH_123456, "PROFESOR_JEFE"),
                (3, "Constanza Rodriguez", "coni.convivencia@liceo.cl", HASH_123456, "CONVIVENCIA_ESCOLAR"),
                (4, "Ignacio Pino", "ignacio.utp@liceo.cl", HASH_123456, "UTP"),
            ],
        )
        conexion.executemany(
            "INSERT INTO Curso (id, nombre, nivel, letra, anio_lectivo, id_profesor_jefe, total_estudiantes)"
            " VALUES (?,?,?,?,?,?,?)",
            [
                (101, "1° Medio A", "Enseñanza Media", "A", 2026, 2, 1),
                (102, "2° Medio B", "Enseñanza Media", "B", 2026, 2, 1),
                (103, "3° Medio A", "Enseñanza Media", "A", 2026, 1, 1),
            ],
        )
        conexion.executemany(
            "INSERT INTO Estudiante (id, rut, nombres, apellidos, id_curso, nivel_riesgo_actual) VALUES (?,?,?,?,?,?)",
            [
                (1, "20.111.222-3", "Ana", "Soto Pérez", 101, "BAJO"),
                (2, "19.333.444-5", "Luis", "Rojas Muñoz", 102, "ALTO"),
                (3, "21.555.666-7", "Sofía", "Vega Contreras", 103, "MEDIO"),
            ],
        )
        # Registros académicos de ejemplo: notas 1.0-7.0 y asistencia %
        conexion.executemany(
            "INSERT INTO RegistroAcademico (id_estudiante, fecha, asistencia, nota) VALUES (?,?,?,?)",
            [
                (1, "2026-08-15", 96.0, 6.5),
                (1, "2026-09-15", 94.0, 6.2),
                (2, "2026-08-15", 78.0, 4.1),
                (2, "2026-09-15", 74.0, 3.8),
                (3, "2026-08-15", 88.0, 5.4),
                (3, "2026-09-15", 85.0, 5.0),
            ],
        )
        conexion.commit()

    conexion.close()
