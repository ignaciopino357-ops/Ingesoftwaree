# API/services/curso_service.py
# Capa de lógica de negocio (reglas de CU-01 / HU 1)

from typing import Any, Dict

from API.repositories.curso_repository import CursoRepository


class UsuarioNoEncontradoException(Exception):
    """El docente consultado no existe en la base de datos."""


class CursoService:
    def __init__(self, repositorio: CursoRepository = None):
        self.repositorio = repositorio or CursoRepository()

    def obtener_cursos_por_docente(self, docente_id: int) -> Dict[str, Any]:
        # Regla 1: el usuario debe existir
        if not self.repositorio.existe_usuario(docente_id):
            raise UsuarioNoEncontradoException(f"El docente con ID {docente_id} no se encuentra registrado.")

        cursos = self.repositorio.obtener_por_docente_id(docente_id)

        # Regla 2: docente sin cursos asignados (criterio alternativo CU-01)
        if not cursos:
            return {
                "exito": True,
                "tiene_carga": False,
                "mensaje": "Actualmente no tiene cursos asignados. Contacte a U.T.P.",
                "total_cursos": 0,
                "cursos": [],
            }

        # Regla 3: happy path
        return {"exito": True, "tiene_carga": True, "mensaje": None,
                "total_cursos": len(cursos), "cursos": cursos}
