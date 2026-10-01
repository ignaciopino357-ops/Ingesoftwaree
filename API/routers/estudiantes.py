# API/routers/estudiantes.py
from fastapi import APIRouter, HTTPException, status

from API.schemas.estudiante import NuevoEstudiante
from API.services.estudiante_service import (
    CursoNoEncontradoException,
    EstudianteDuplicadoException,
    EstudianteNoEncontradoException,
    EstudianteService,
)

router = APIRouter(tags=["Estudiantes"])
servicio = EstudianteService()


# Importante: esta ruta fija debe declararse ANTES de /api/estudiantes/{estudiante_id}
@router.get("/api/estudiantes/lista-demo", summary="Lista de alumnos de ejemplo para el login")
def lista_demo():
    return {"exito": True, "estudiantes": servicio.listar_alumnos_ejemplo()}


@router.get("/api/estudiantes/{estudiante_id}", summary="Portal del alumno: su curso y sus notas")
def portal_estudiante(estudiante_id: int):
    try:
        return servicio.obtener_portal_estudiante(estudiante_id)
    except EstudianteNoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/api/cursos/{curso_id}/estudiantes", summary="Alumnos de un curso con notas y asistencia")
def estudiantes_del_curso(curso_id: int):
    try:
        return servicio.obtener_curso_con_estudiantes(curso_id)
    except CursoNoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/api/estudiantes", status_code=status.HTTP_201_CREATED,
             summary="Crear un alumno nuevo (contraseña inicial: 123456)")
def crear_estudiante(datos: NuevoEstudiante):
    try:
        return servicio.crear_estudiante(datos.rut, datos.nombres, datos.apellidos, datos.email, datos.id_curso)
    except CursoNoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except EstudianteDuplicadoException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
