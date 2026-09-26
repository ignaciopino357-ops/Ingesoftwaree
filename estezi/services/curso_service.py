# API/services/curso_service.py
# Capa de Lógica de Negocio (Reglas de CU-01 / HU 1) - Punto 10.21

from repositories.curso_repository import CursoRepository
from typing import Dict, Any

class UsuarioNoEncontradoException(Exception):
    """Excepción lanzada cuando el docente consultado no existe en la base de datos."""
    pass

class CursoService:
    """Implementa las reglas de negocio y validaciones del caso de uso CU-01."""

    def __init__(self, repositorio: CursoRepository = None):
        self.repositorio = repositorio or CursoRepository()

    def obtener_cursos_por_docente(self, docente_id: int) -> Dict[str, Any]:
        """Aplica las reglas de negocio del CU-01 para la carga académica."""
        # Regla 1: Validar existencia del usuario en la institución
        if not self.repositorio.existe_usuario(docente_id):
            raise UsuarioNoEncontradoException(f"El docente con ID {docente_id} no se encuentra registrado.")

        # Obtener los cursos desde la persistencia SQLite
        cursos = self.repositorio.obtener_por_docente_id(docente_id)

        # Regla 2: Docente sin cursos asignados (Criterio alternativo CU-01)
        if not cursos:
            return {
                "exito": True,
                "tiene_carga": False,
                "mensaje": "Actualmente no tiene cursos asignados. Contacte a U.T.P.",
                "total_cursos": 0,
                "cursos": []
            }

        # Regla 3: Docente con cursos asignados (Happy Path CU-01)
        return {
            "exito": True,
            "tiene_carga": True,
            "mensaje": None,
            "total_cursos": len(cursos),
            "cursos": cursos
        }