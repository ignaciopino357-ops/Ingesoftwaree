# API/repositories/estudiante_repository.py
from typing import Any, Dict, List, Optional

from API.database import conexion_bd

# Nunca se usa SELECT * sobre Estudiante: incluiría password_hash en las respuestas de la API.
COLUMNAS_PUBLICAS = "e.id, e.rut, e.nombres, e.apellidos, e.email, e.id_curso, e.nivel_riesgo_actual"


class EstudianteRepository:

    @staticmethod
    def obtener_por_id(estudiante_id: int) -> Optional[Dict[str, Any]]:
        with conexion_bd() as con:
            est = con.execute(
                f"SELECT {COLUMNAS_PUBLICAS} FROM Estudiante e WHERE e.id = ?", (estudiante_id,)
            ).fetchone()
            if not est:
                return None
            curso = con.execute("SELECT * FROM Curso WHERE id = ?", (est["id_curso"],)).fetchone()
            registros = con.execute(
                """
                SELECT ra.fecha, ra.asistencia, ra.nota, a.nombre AS asignatura
                FROM RegistroAcademico ra
                LEFT JOIN Asignatura a ON a.id = ra.id_asignatura
                WHERE ra.id_estudiante = ?
                ORDER BY ra.fecha, ra.id
                """,
                (estudiante_id,),
            ).fetchall()
        return {
            "estudiante": dict(est),
            "curso": dict(curso) if curso else None,
            "registros": [dict(r) for r in registros],
        }

    @staticmethod
    def listar_alumnos_ejemplo() -> List[Dict[str, Any]]:
        """Para el selector del login de alumno: id, nombre y curso."""
        with conexion_bd() as con:
            filas = con.execute(
                "SELECT e.id, e.nombres, e.apellidos, c.nombre AS curso "
                "FROM Estudiante e JOIN Curso c ON c.id = e.id_curso ORDER BY e.id"
            ).fetchall()
        return [dict(f) for f in filas]

    @staticmethod
    def obtener_por_curso(curso_id: int) -> Optional[Dict[str, Any]]:
        """Curso + sus alumnos con promedio de notas y asistencia (una sola consulta)."""
        with conexion_bd() as con:
            curso = con.execute("SELECT * FROM Curso WHERE id = ?", (curso_id,)).fetchone()
            if not curso:
                return None
            filas = con.execute(
                f"""
                SELECT {COLUMNAS_PUBLICAS},
                       ROUND(AVG(ra.nota), 1)       AS promedio_notas,
                       ROUND(AVG(ra.asistencia), 1) AS promedio_asistencia
                FROM Estudiante e
                LEFT JOIN RegistroAcademico ra ON ra.id_estudiante = e.id
                WHERE e.id_curso = ?
                GROUP BY e.id
                ORDER BY e.apellidos, e.nombres
                """,
                (curso_id,),
            ).fetchall()
        return {"curso": dict(curso), "estudiantes": [dict(f) for f in filas]}

    @staticmethod
    def obtener_estadisticas_curso(curso_id: int) -> Optional[Dict[str, Any]]:
        """Promedio de notas y % de asistencia por curso."""
        with conexion_bd() as con:
            curso = con.execute("SELECT * FROM Curso WHERE id = ?", (curso_id,)).fetchone()
            if not curso:
                return None
            fila = con.execute(
                """
                SELECT
                    ROUND(AVG(ra.nota), 1)        AS promedio_notas_curso,
                    ROUND(AVG(ra.asistencia), 1)  AS porcentaje_asistencia_curso,
                    COUNT(DISTINCT e.id)          AS total_estudiantes,
                    COUNT(ra.id)                  AS total_registros
                FROM Estudiante e
                LEFT JOIN RegistroAcademico ra ON ra.id_estudiante = e.id
                WHERE e.id_curso = ?
                """,
                (curso_id,),
            ).fetchone()
        return {"curso": dict(curso), **dict(fila)}

    # ---- escritura / validaciones de alta ----
    @staticmethod
    def existe_rut(rut: str) -> bool:
        with conexion_bd() as con:
            return con.execute("SELECT 1 FROM Estudiante WHERE rut = ?", (rut,)).fetchone() is not None

    @staticmethod
    def existe_email(email: str) -> bool:
        """El correo debe ser único entre alumnos Y usuarios (es el identificador de login)."""
        with conexion_bd() as con:
            return con.execute(
                "SELECT 1 FROM Estudiante WHERE email = ? UNION SELECT 1 FROM Usuario WHERE email = ?",
                (email, email),
            ).fetchone() is not None

    @staticmethod
    def crear(rut: str, nombres: str, apellidos: str, email: str, password_hash: str, id_curso: int) -> int:
        with conexion_bd() as con:
            cur = con.execute(
                "INSERT INTO Estudiante (rut, nombres, apellidos, email, password_hash, id_curso) "
                "VALUES (?,?,?,?,?,?)",
                (rut, nombres, apellidos, email, password_hash, id_curso),
            )
            con.execute(
                "UPDATE Curso SET total_estudiantes = "
                "(SELECT COUNT(*) FROM Estudiante WHERE id_curso = ?) WHERE id = ?",
                (id_curso, id_curso),
            )
            return cur.lastrowid
