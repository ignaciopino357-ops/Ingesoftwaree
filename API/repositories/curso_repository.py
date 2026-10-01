# API/repositories/curso_repository.py
# Capa de acceso a datos (SQLite) para Curso y Usuario.

from typing import Any, Dict, List

from API.database import conexion_bd


class CursoRepository:
    """Encapsula las consultas SQL a las tablas Curso y Usuario."""

    @staticmethod
    def obtener_por_docente_id(docente_id: int) -> List[Dict[str, Any]]:
        with conexion_bd() as con:
            filas = con.execute(
                """
                SELECT id, nombre, nivel, letra, anio_lectivo, id_profesor_jefe, total_estudiantes
                FROM Curso
                WHERE id_profesor_jefe = ?
                ORDER BY nombre, id
                """,
                (docente_id,),
            ).fetchall()
        return [dict(fila) for fila in filas]

    @staticmethod
    def existe_usuario(usuario_id: int) -> bool:
        with conexion_bd() as con:
            return con.execute("SELECT 1 FROM Usuario WHERE id = ?", (usuario_id,)).fetchone() is not None

    @staticmethod
    def existe_curso(curso_id: int) -> bool:
        with conexion_bd() as con:
            return con.execute("SELECT 1 FROM Curso WHERE id = ?", (curso_id,)).fetchone() is not None
