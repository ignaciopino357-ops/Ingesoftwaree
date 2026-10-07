"""Consultas a la base de datos que usan varios portales."""
from datetime import date
from typing import Optional

from app.db import conexion
from app.riesgo import ORDEN_RIESGO, calcular_riesgo, porcentaje_asistencia, promedio_general

NUM_EVALUACIONES = 6


# ---------- Calendario (HU-03) ----------

def obtener_semestre() -> tuple:
    """Devuelve (inicio, fin) como date, o (None, None) si no está configurado."""
    with conexion() as conn:
        fila = conn.execute("SELECT inicio, fin FROM semestre WHERE id = 1").fetchone()
    if not fila:
        return None, None
    return date.fromisoformat(fila["inicio"]), date.fromisoformat(fila["fin"])


def obtener_feriados() -> dict:
    """Diccionario {date: nombre} con todos los feriados."""
    with conexion() as conn:
        filas = conn.execute("SELECT fecha, nombre FROM feriados ORDER BY fecha").fetchall()
    return {date.fromisoformat(f["fecha"]): f["nombre"] for f in filas}


# ---------- Cursos y alumnos ----------

def obtener_curso(curso_id: int) -> Optional[dict]:
    with conexion() as conn:
        fila = conn.execute(
            """SELECT c.id, c.nombre, c.profesor_id, u.nombre AS profesor
               FROM cursos c LEFT JOIN usuarios u ON u.id = c.profesor_id
               WHERE c.id = ?""",
            (curso_id,),
        ).fetchone()
    return dict(fila) if fila else None


def cursos_del_profesor(profesor_id: int) -> list:
    with conexion() as conn:
        filas = conn.execute(
            "SELECT id, nombre FROM cursos WHERE profesor_id = ? ORDER BY nombre", (profesor_id,)
        ).fetchall()
    return [dict(f) for f in filas]


def alumnos_del_curso(curso_id: int) -> list:
    with conexion() as conn:
        filas = conn.execute(
            """SELECT u.id, u.nombre FROM alumnos_curso ac
               JOIN usuarios u ON u.id = ac.alumno_id
               WHERE ac.curso_id = ? ORDER BY u.nombre""",
            (curso_id,),
        ).fetchall()
    return [dict(f) for f in filas]


def asignaturas() -> list:
    with conexion() as conn:
        return [dict(f) for f in conn.execute("SELECT id, nombre FROM asignaturas ORDER BY id")]


# ---------- Notas (HU-05) ----------

def notas_del_alumno(alumno_id: int) -> dict:
    """{nombre_asignatura: [notas en orden de evaluación]}"""
    with conexion() as conn:
        filas = conn.execute(
            """SELECT a.nombre, n.nota FROM notas n
               JOIN asignaturas a ON a.id = n.asignatura_id
               WHERE n.alumno_id = ? ORDER BY a.id, n.numero""",
            (alumno_id,),
        ).fetchall()
    resultado = {}
    for f in filas:
        resultado.setdefault(f["nombre"], []).append(f["nota"])
    return resultado


def notas_de_asignatura(curso_id: int, asignatura_id: int) -> dict:
    """{alumno_id: {numero: nota}} para la tabla editable."""
    with conexion() as conn:
        filas = conn.execute(
            """SELECT n.alumno_id, n.numero, n.nota FROM notas n
               JOIN alumnos_curso ac ON ac.alumno_id = n.alumno_id
               WHERE ac.curso_id = ? AND n.asignatura_id = ?""",
            (curso_id, asignatura_id),
        ).fetchall()
    resultado = {}
    for f in filas:
        resultado.setdefault(f["alumno_id"], {})[f["numero"]] = f["nota"]
    return resultado


# ---------- Asistencia (HU-06) ----------

def asistencia_del_alumno(alumno_id: int) -> list:
    with conexion() as conn:
        filas = conn.execute(
            "SELECT fecha, estado FROM asistencia WHERE alumno_id = ? ORDER BY fecha DESC",
            (alumno_id,),
        ).fetchall()
    return [dict(f) for f in filas]


def asistencia_del_dia(curso_id: int, fecha: str) -> dict:
    """{alumno_id: estado} para una fecha."""
    with conexion() as conn:
        filas = conn.execute(
            """SELECT a.alumno_id, a.estado FROM asistencia a
               JOIN alumnos_curso ac ON ac.alumno_id = a.alumno_id
               WHERE ac.curso_id = ? AND a.fecha = ?""",
            (curso_id, fecha),
        ).fetchall()
    return {f["alumno_id"]: f["estado"] for f in filas}


def conteo_asistencia(alumno_id: int) -> dict:
    with conexion() as conn:
        filas = conn.execute(
            "SELECT estado, COUNT(*) AS n FROM asistencia WHERE alumno_id = ? GROUP BY estado",
            (alumno_id,),
        ).fetchall()
    conteo = {"P": 0, "A": 0, "J": 0}
    for f in filas:
        conteo[f["estado"]] = f["n"]
    return conteo


def fechas_con_asistencia(curso_id: int) -> list:
    with conexion() as conn:
        filas = conn.execute(
            """SELECT DISTINCT a.fecha FROM asistencia a
               JOIN alumnos_curso ac ON ac.alumno_id = a.alumno_id
               WHERE ac.curso_id = ? ORDER BY a.fecha""",
            (curso_id,),
        ).fetchall()
    return [f["fecha"] for f in filas]


# ---------- Resumen del curso con riesgo (HU-04 + HU-07) ----------

def resumen_alumno(alumno: dict) -> dict:
    conteo = conteo_asistencia(alumno["id"])
    asistencia = porcentaje_asistencia(conteo["P"], conteo["A"], conteo["J"])
    promedio = promedio_general(notas_del_alumno(alumno["id"]))
    riesgo = calcular_riesgo(asistencia, promedio)
    return {
        **alumno,
        "asistencia": asistencia,
        "promedio": promedio,
        "riesgo": riesgo.estado,
        "motivo": riesgo.motivo,
        "conteo": conteo,
    }


ORDENES = {
    "riesgo": lambda a: (ORDEN_RIESGO[a["riesgo"]], a["nombre"]),
    "nombre": lambda a: a["nombre"],
    "promedio": lambda a: (a["promedio"] is None, a["promedio"] or 0),
    "asistencia": lambda a: (a["asistencia"] is None, a["asistencia"] or 0),
}


def resumen_curso(curso_id: int, orden: str = "riesgo") -> list:
    filas = [resumen_alumno(a) for a in alumnos_del_curso(curso_id)]
    return sorted(filas, key=ORDENES.get(orden, ORDENES["riesgo"]))
