# API/routers/cursos.py
# Controlador de Rutas / Adaptador de Entrada HTTP (Punto 10.21 de la guía)

from fastapi import APIRouter, HTTPException, Query, status
from schemas.curso import ConsultaCursosRespuesta
from services.curso_service import CursoService, UsuarioNoEncontradoException

router = APIRouter(
    prefix="/api/cursos",
    tags=["Cursos"]
)

# Inyección de la capa de servicio
servicio_curso = CursoService()

@router.get(
    "",
    response_model=ConsultaCursosRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Listar cursos asignados por docente",
    description="Implementa el endpoint principal para HU 1 y caso de uso CU-01."
)
def listar_cursos_por_docente(
    docente_id: int = Query(
        ...,
        ge=1,
        description="Identificador numérico del docente en el sistema escolar"
    )
):
    """
    Endpoint: GET /api/cursos?docente_id={id}
    - 200 OK: Retorna la estructura de cursos asignados o bandera tiene_carga = False.
    - 404 Not Found: El docente_id no existe en la base de datos.
    - 422 Unprocessable Entity: Validación automática si docente_id no es entero positivo.
    - 500 Internal Server Error: Excepción no controlada a nivel de persistencia o servidor.
    """
    try:
        resultado = servicio_curso.obtener_cursos_por_docente(docente_id)
        return resultado

    except UsuarioNoEncontradoException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al consultar asignación de cursos."
        )