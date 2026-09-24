# API/database.py
# Configuración y persistencia SQLite (Punto 10.15 y 10.16 de la guía)

import sqlite3

DB_NAME = "sprint1.db"

def obtener_conexion():
    """Retorna una conexión a la base de datos con acceso a columnas por nombre."""
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    return conexion

def inicializar_base_datos():
    """Crea las tablas e inserta los datos iniciales de prueba para la HU 1."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Tabla de Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            rol TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Tabla de Cursos asignados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Curso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            nivel TEXT NOT NULL,
            letra TEXT NOT NULL,
            anio_lectivo INTEGER NOT NULL,
            id_profesor_jefe INTEGER,
            total_estudiantes INTEGER DEFAULT 0,
            FOREIGN KEY (id_profesor_jefe) REFERENCES Usuario(id)
        )
    """)

    conexion.commit()

    # Precarga de datos de prueba si la tabla Usuario está vacía
    cursor.execute("SELECT COUNT(*) AS total FROM Usuario")
    if cursor.fetchone()["total"] == 0:
        cursor.executemany("""
            INSERT INTO Usuario (id, nombre_completo, email, rol) VALUES (?, ?, ?, ?)
        """, [
            (1, "Diego Rubilar", "diego.docente@liceo.cl", "DOCENTE"),
            (2, "Mirko Massa", "mirko.jefe@liceo.cl", "PROFESOR_JEFE"),
            (3, "Constanza Rodriguez", "coni.convivencia@liceo.cl", "CONVIVENCIA_ESCOLAR"),
            (4, "Ignacio Pino", "ignacio.utp@liceo.cl", "UTP")
        ])

        cursor.executemany("""
            INSERT INTO Curso (id, nombre, nivel, letra, anio_lectivo, id_profesor_jefe, total_estudiantes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            (101, "1° Medio A", "Enseñanza Media", "A", 2026, 2, 32),
            (102, "2° Medio B", "Enseñanza Media", "B", 2026, 2, 28),
            (103, "3° Medio A", "Enseñanza Media", "A", 2026, 1, 30)
        ])
        conexion.commit()

    conexion.close()