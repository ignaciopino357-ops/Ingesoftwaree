# API/routers/cursos.py
# Controlador de rutas / adaptador de entrada HTTP

from fastapi import APIRouter, HTTPException, Query, status

from API.schemas.curso import ConsultaCursosRespuesta
from API.services.curso_service import CursoService, UsuarioNoEncontradoException

router = APIRouter(prefix="/api/cursos", tags=["Cursos"])
servicio_curso = CursoService()


@router.get(
    "",
    response_model=ConsultaCursosRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Listar cursos asignados por docente",
    description="Endpoint principal para HU 1 y caso de uso CU-01.",
)
def listar_cursos_por_docente(
    docente_id: int = Query(..., ge=1, description="Identificador numérico del docente")
):
    """
    GET /api/cursos?docente_id={id}
    - 200: cursos asignados, o tiene_carga = False si no tiene.
    - 404: el docente_id no existe.
    - 422: docente_id no es un entero positivo (validación automática).
    Cualquier otro error lo maneja FastAPI como 500 (y queda en el log del servidor).
    """
    try:
        return servicio_curso.obtener_cursos_por_docente(docente_id)
    except UsuarioNoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
