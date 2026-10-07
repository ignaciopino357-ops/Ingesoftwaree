"""Datos de prueba para la demo.

Uso:
    python -m app.seed          -> carga datos solo si la base está vacía
    python -m app.seed --reset  -> borra la base y la vuelve a crear

Todos los nombres son inventados. Los feriados son de ejemplo:
la directiva debe revisarlos en el portal antes de usar el sistema.
"""
import os
import sys
from datetime import date

from app import db
from app.auth import hashear_clave
from app.calendario import dias_de_clases

SEMESTRE = (date(2026, 7, 27), date(2026, 12, 4))
FERIADOS = [
    (date(2026, 8, 15), "Asunción de la Virgen"),
    (date(2026, 9, 18), "Independencia Nacional"),
    (date(2026, 9, 19), "Glorias del Ejército"),
    (date(2026, 10, 12), "Encuentro de Dos Mundos"),
    (date(2026, 10, 31), "Día de las Iglesias Evangélicas"),
    (date(2026, 11, 1), "Día de Todos los Santos"),
    (date(2026, 12, 8), "Inmaculada Concepción"),
]
ASIGNATURAS = ["Lenguaje", "Matemática", "Historia", "Inglés", "Módulo de especialidad"]

ALUMNOS = [
    # (usuario, nombre, curso, tasa de ausencia, nota base)  -> perfil esperado
    ("alumno1", "Ana Contreras", "3° Medio A", 0.02, 5.9),    # Bajo
    ("alumno2", "Benjamín Rojas", "3° Medio A", 0.05, 5.4),   # Bajo
    ("alumno3", "Camila Fuentes", "3° Medio A", 0.22, 5.1),   # Medio (asistencia)
    ("alumno4", "Diego Sepúlveda", "3° Medio A", 0.04, 3.6),  # Medio (promedio)
    ("alumno5", "Emilia Vargas", "3° Medio A", 0.28, 3.4),    # Alto
    ("alumno6", "Felipe Araya", "3° Medio A", 0.08, 4.9),     # Bajo
    ("alumno7", "Gabriela Torres", "3° Medio A", 0.03, 6.2),  # Bajo
    ("alumno8", "Hugo Navarro", "3° Medio A", None, None),    # Sin datos (recién llegado)
    ("alumno9", "Isidora Pérez", "3° Medio B", 0.06, 5.0),
    ("alumno10", "Joaquín Díaz", "3° Medio B", 0.18, 4.2),
    ("alumno11", "Karla Morales", None, None, None),           # sin curso: para probar HU-02
    ("alumno12", "Lucas Herrera", None, None, None),           # sin curso
]

DESVIOS = [-0.4, 0.3, 0.1]  # se suman a la nota base para tener 3 evaluaciones distintas


def cargar_datos_de_prueba() -> None:
    with db.conexion() as conn:
        def crear_usuario(usuario, nombre, rol, clave):
            cur = conn.execute(
                "INSERT INTO usuarios (nombre, usuario, clave_hash, rol) VALUES (?, ?, ?, ?)",
                (nombre, usuario, hashear_clave(clave), rol),
            )
            return cur.lastrowid

        crear_usuario("directiva", "María Soto", "directiva", "directiva123")
        prof_a = crear_usuario("pjara", "Pedro Jara", "profesor", "profe123")
        prof_b = crear_usuario("cmunoz", "Carolina Muñoz", "profesor", "profe123")
        crear_usuario("pnuevo", "Rodrigo Pizarro", "profesor", "profe123")  # sin curso

        cursos = {}
        for nombre, prof in [("3° Medio A", prof_a), ("3° Medio B", prof_b)]:
            cursos[nombre] = conn.execute(
                "INSERT INTO cursos (nombre, profesor_id) VALUES (?, ?)", (nombre, prof)
            ).lastrowid

        asignaturas = [
            conn.execute("INSERT INTO asignaturas (nombre) VALUES (?)", (a,)).lastrowid
            for a in ASIGNATURAS
        ]

        conn.execute("INSERT INTO semestre (id, inicio, fin) VALUES (1, ?, ?)",
                     (SEMESTRE[0].isoformat(), SEMESTRE[1].isoformat()))
        conn.executemany("INSERT INTO feriados (fecha, nombre) VALUES (?, ?)",
                         [(f.isoformat(), n) for f, n in FERIADOS])

        # Asistencia ya registrada: días de clases del 1 de septiembre al 6 de octubre
        dias = dias_de_clases(date(2026, 9, 1), date(2026, 10, 6), [f for f, _ in FERIADOS])

        for i, (usuario, nombre, curso, ausencia, base) in enumerate(ALUMNOS, start=1):
            alumno_id = crear_usuario(usuario, nombre, "alumno", "alumno123")
            if curso:
                conn.execute("INSERT INTO alumnos_curso (alumno_id, curso_id) VALUES (?, ?)",
                             (alumno_id, cursos[curso]))
            if ausencia is None:
                continue
            faltas = 0
            for d, dia in enumerate(dias):
                # Reparte las faltas de forma pareja según la tasa; 1 de cada 3 queda justificada
                if int((d + 1 + i) * ausencia) > int((d + i) * ausencia):
                    faltas += 1
                    estado = "J" if faltas % 3 == 0 else "A"
                else:
                    estado = "P"
                conn.execute("INSERT INTO asistencia (alumno_id, fecha, estado) VALUES (?, ?, ?)",
                             (alumno_id, dia.isoformat(), estado))
            for a, asig_id in enumerate(asignaturas):
                for numero, desvio in enumerate(DESVIOS, start=1):
                    nota = round(min(7.0, max(1.0, base + desvio + (a - 2) * 0.1)), 1)
                    conn.execute(
                        "INSERT INTO notas (alumno_id, asignatura_id, numero, nota) VALUES (?, ?, ?, ?)",
                        (alumno_id, asig_id, numero, nota),
                    )


if __name__ == "__main__":
    if "--reset" in sys.argv and os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
        print(f"Base {db.DB_PATH} borrada.")
    db.crear_tablas()
    if db.esta_vacia():
        cargar_datos_de_prueba()
        print("Datos de prueba cargados.")
    else:
        print("La base ya tenía datos; no se cargó nada. Use --reset para empezar de cero.")
