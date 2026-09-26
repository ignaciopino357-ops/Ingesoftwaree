# API/repositories/curso_repository.py
# Capa de Acceso a Datos (Persistencia SQLite) - Punto 10.21

from database import obtener_conexion
from typing import List, Dict, Any, Optional

class CursoRepository:
    """Encapsula el acceso y las consultas SQL a la tabla Curso y Usuario."""

    @staticmethod
    def obtener_por_docente_id(docente_id: int) -> List[Dict[str, Any]]:
        """Consulta en SQLite todos los cursos asignados a un docente específico."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        query = """
            SELECT 
                id, 
                nombre, 
                nivel, 
                letra, 
                anio_lectivo, 
                id_profesor_jefe, 
                total_estudiantes
            FROM Curso
            WHERE id_profesor_jefe = ?
        """
        cursor.execute(query, (docente_id,))
        filas = cursor.fetchall()
        conexion.close()

        # Conversión de sqlite3.Row a diccionarios estándar para Pydantic
        return [dict(fila) for fila in filas]

    @staticmethod
    def existe_usuario(usuario_id: int) -> bool:
        """Verifica en SQLite si el identificador corresponde a un usuario registrado."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM Usuario WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        conexion.close()

        return usuario is not None