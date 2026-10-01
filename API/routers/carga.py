# API/routers/carga.py
# Endpoints de las Tareas: carga masiva, estadísticas por curso y exportación de reporte.

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from API.excepciones import CursoNoEncontradoException
from API.services.carga_service import CargaService, ArchivoInvalidoException
from API.services.reporte_service import ReporteService
from API.repositories.estudiante_repository import EstudianteRepository

router = APIRouter(tags=["Carga y Reportes"])
servicio_carga = CargaService()
servicio_reporte = ReporteService()

TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB


@router.post("/api/cursos/{curso_id}/cargar-notas", summary="Carga masiva de notas/asistencia desde Excel o CSV")
async def cargar_notas(curso_id: int, archivo: UploadFile = File(...)):
    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="El archivo supera el máximo de 5 MB.")
    try:
        return servicio_carga.procesar_carga(curso_id, archivo.filename or "", contenido)
    except ArchivoInvalidoException as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except CursoNoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/api/cursos/{curso_id}/estadisticas", summary="Promedio de notas y % de asistencia del curso")
def estadisticas_curso(curso_id: int):
    datos = EstudianteRepository.obtener_estadisticas_curso(curso_id)
    if not datos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El curso {curso_id} no existe.")
    return {"exito": True, **datos}


@router.get("/api/cursos/{curso_id}/exportar", summary="Descargar reporte del curso (csv o xlsx)")
def exportar_curso(curso_id: int, formato: str = "xlsx"):
    if formato == "csv":
        contenido, nombre = servicio_reporte.generar_csv(curso_id)
        media_type = "text/csv"
    elif formato == "xlsx":
        contenido, nombre = servicio_reporte.generar_excel(curso_id)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(status_code=422, detail="formato debe ser 'csv' o 'xlsx'")

    if contenido is None:
        raise HTTPException(status_code=404, detail=f"El curso {curso_id} no existe.")

    return Response(
        content=contenido, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
