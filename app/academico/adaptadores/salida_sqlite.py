"""Módulo Gestión Académica · ADAPTADORES DE SALIDA: repositorios SQLite.

Único lugar del módulo donde hay SQL. Implementan los puertos de app/academico/puertos.py.
"""
from datetime import date
from typing import Optional

from app.academico.dominio import Alumno, Curso
from app.academico.puertos import (
    RepositorioAsistencia, RepositorioCalendario, RepositorioCursos, RepositorioNotas,
)
from app.compartido.db import conexion

_SQL_CURSO = """SELECT c.id, c.nombre, c.profesor_id, u.nombre AS profesor
                FROM cursos c LEFT JOIN usuarios u ON u.id = c.profesor_id"""


def _a_curso(fila) -> Curso:
    return Curso(id=fila["id"], nombre=fila["nombre"], profesor_id=fila["profesor_id"], profesor=fila["profesor"])


class RepositorioCursosSQLite(RepositorioCursos):
    def obtener(self, curso_id: int) -> Optional[Curso]:
        with conexion() as conn:
            fila = conn.execute(f"{_SQL_CURSO} WHERE c.id = ?", (curso_id,)).fetchone()
        return _a_curso(fila) if fila else None

    def listar(self) -> list[Curso]:
        with conexion() as conn:
            return [_a_curso(f) for f in conn.execute(f"{_SQL_CURSO} ORDER BY c.nombre")]

    def listar_de_profesor(self, profesor_id: int) -> list[Curso]:
        with conexion() as conn:
            filas = conn.execute(f"{_SQL_CURSO} WHERE c.profesor_id = ? ORDER BY c.nombre", (profesor_id,))
            return [_a_curso(f) for f in filas]

    def existe_nombre(self, nombre: str) -> bool:
        with conexion() as conn:
            return conn.execute("SELECT 1 FROM cursos WHERE nombre = ?", (nombre,)).fetchone() is not None

    def crear(self, nombre: str, profesor_id: Optional[int]) -> int:
        with conexion() as conn:
            return conn.execute("INSERT INTO cursos (nombre, profesor_id) VALUES (?, ?)",
                                (nombre, profesor_id)).lastrowid

    def asignar_profesor(self, curso_id: int, profesor_id: Optional[int]) -> None:
        with conexion() as conn:
            conn.execute("UPDATE cursos SET profesor_id = ? WHERE id = ?", (profesor_id, curso_id))

    def alumnos(self, curso_id: int) -> list[Alumno]:
        with conexion() as conn:
            filas = conn.execute(
                """SELECT u.id, u.nombre FROM alumnos_curso ac JOIN usuarios u ON u.id = ac.alumno_id
                   WHERE ac.curso_id = ? ORDER BY u.nombre""", (curso_id,)).fetchall()
        return [Alumno(f["id"], f["nombre"]) for f in filas]

    def todos_los_alumnos(self) -> list[tuple[Alumno, Optional[str]]]:
        with conexion() as conn:
            filas = conn.execute(
                """SELECT u.id, u.nombre, c.nombre AS curso FROM usuarios u
                   LEFT JOIN alumnos_curso ac ON ac.alumno_id = u.id
                   LEFT JOIN cursos c ON c.id = ac.curso_id
                   WHERE u.rol = 'alumno' ORDER BY c.nombre IS NOT NULL, u.nombre""").fetchall()
        return [(Alumno(f["id"], f["nombre"]), f["curso"]) for f in filas]

    def curso_de_alumno(self, alumno_id: int) -> Optional[str]:
        with conexion() as conn:
            fila = conn.execute(
                """SELECT c.nombre FROM alumnos_curso ac JOIN cursos c ON c.id = ac.curso_id
                   WHERE ac.alumno_id = ?""", (alumno_id,)).fetchone()
        return fila["nombre"] if fila else None

    def agregar_alumno(self, curso_id: int, alumno_id: int) -> None:
        with conexion() as conn:
            conn.execute("INSERT INTO alumnos_curso (alumno_id, curso_id) VALUES (?, ?)", (alumno_id, curso_id))

    def quitar_alumno(self, curso_id: int, alumno_id: int) -> None:
        with conexion() as conn:
            conn.execute("DELETE FROM alumnos_curso WHERE alumno_id = ? AND curso_id = ?", (alumno_id, curso_id))


class RepositorioNotasSQLite(RepositorioNotas):
    def asignaturas(self) -> list[dict]:
        with conexion() as conn:
            return [dict(f) for f in conn.execute("SELECT id, nombre FROM asignaturas ORDER BY id")]

    def de_alumno(self, alumno_id: int) -> dict:
        with conexion() as conn:
            filas = conn.execute(
                """SELECT a.nombre, n.nota FROM notas n JOIN asignaturas a ON a.id = n.asignatura_id
                   WHERE n.alumno_id = ? ORDER BY a.id, n.numero""", (alumno_id,)).fetchall()
        resultado = {}
        for f in filas:
            resultado.setdefault(f["nombre"], []).append(f["nota"])
        return resultado

    def de_asignatura(self, curso_id: int, asignatura_id: int) -> dict:
        with conexion() as conn:
            filas = conn.execute(
                """SELECT n.alumno_id, n.numero, n.nota FROM notas n
                   JOIN alumnos_curso ac ON ac.alumno_id = n.alumno_id
                   WHERE ac.curso_id = ? AND n.asignatura_id = ?""", (curso_id, asignatura_id)).fetchall()
        resultado = {}
        for f in filas:
            resultado.setdefault(f["alumno_id"], {})[f["numero"]] = f["nota"]
        return resultado

    def guardar(self, asignatura_id: int, cambios: list[tuple[int, int, Optional[float]]]) -> None:
        with conexion() as conn:
            for alumno_id, numero, nota in cambios:
                if nota is None:
                    conn.execute("DELETE FROM notas WHERE alumno_id = ? AND asignatura_id = ? AND numero = ?",
                                 (alumno_id, asignatura_id, numero))
                else:
                    conn.execute(
                        """INSERT INTO notas (alumno_id, asignatura_id, numero, nota) VALUES (?, ?, ?, ?)
                           ON CONFLICT (alumno_id, asignatura_id, numero) DO UPDATE SET nota = excluded.nota""",
                        (alumno_id, asignatura_id, numero, nota))


class RepositorioAsistenciaSQLite(RepositorioAsistencia):
    def de_alumno(self, alumno_id: int) -> list[tuple[str, str]]:
        with conexion() as conn:
            filas = conn.execute("SELECT fecha, estado FROM asistencia WHERE alumno_id = ? ORDER BY fecha DESC",
                                 (alumno_id,)).fetchall()
        return [(f["fecha"], f["estado"]) for f in filas]

    def conteo(self, alumno_id: int) -> dict:
        conteo = {"P": 0, "A": 0, "J": 0}
        with conexion() as conn:
            for f in conn.execute("SELECT estado, COUNT(*) AS n FROM asistencia WHERE alumno_id = ? GROUP BY estado",
                                  (alumno_id,)):
                conteo[f["estado"]] = f["n"]
        return conteo

    def del_dia(self, curso_id: int, dia: date) -> dict:
        with conexion() as conn:
            filas = conn.execute(
                """SELECT a.alumno_id, a.estado FROM asistencia a
                   JOIN alumnos_curso ac ON ac.alumno_id = a.alumno_id
                   WHERE ac.curso_id = ? AND a.fecha = ?""", (curso_id, dia.isoformat())).fetchall()
        return {f["alumno_id"]: f["estado"] for f in filas}

    def fechas(self, curso_id: int) -> list[str]:
        with conexion() as conn:
            filas = conn.execute(
                """SELECT DISTINCT a.fecha FROM asistencia a JOIN alumnos_curso ac ON ac.alumno_id = a.alumno_id
                   WHERE ac.curso_id = ? ORDER BY a.fecha""", (curso_id,)).fetchall()
        return [f["fecha"] for f in filas]

    def guardar(self, dia: date, estados: dict) -> None:
        with conexion() as conn:
            for alumno_id, estado in estados.items():
                conn.execute(
                    """INSERT INTO asistencia (alumno_id, fecha, estado) VALUES (?, ?, ?)
                       ON CONFLICT (alumno_id, fecha) DO UPDATE SET estado = excluded.estado""",
                    (alumno_id, dia.isoformat(), estado))


class RepositorioCalendarioSQLite(RepositorioCalendario):
    def semestre(self):
        with conexion() as conn:
            fila = conn.execute("SELECT inicio, fin FROM semestre WHERE id = 1").fetchone()
        if not fila:
            return None, None
        return date.fromisoformat(fila["inicio"]), date.fromisoformat(fila["fin"])

    def guardar_semestre(self, inicio: date, fin: date) -> None:
        with conexion() as conn:
            conn.execute(
                """INSERT INTO semestre (id, inicio, fin) VALUES (1, ?, ?)
                   ON CONFLICT (id) DO UPDATE SET inicio = excluded.inicio, fin = excluded.fin""",
                (inicio.isoformat(), fin.isoformat()))

    def feriados(self) -> dict:
        with conexion() as conn:
            filas = conn.execute("SELECT fecha, nombre FROM feriados ORDER BY fecha").fetchall()
        return {date.fromisoformat(f["fecha"]): f["nombre"] for f in filas}

    def guardar_feriado(self, dia: date, nombre: str) -> None:
        with conexion() as conn:
            conn.execute(
                """INSERT INTO feriados (fecha, nombre) VALUES (?, ?)
                   ON CONFLICT (fecha) DO UPDATE SET nombre = excluded.nombre""", (dia.isoformat(), nombre))

    def eliminar_feriado(self, dia: date) -> None:
        with conexion() as conn:
            conn.execute("DELETE FROM feriados WHERE fecha = ?", (dia.isoformat(),))
