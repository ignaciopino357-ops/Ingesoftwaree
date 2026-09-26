# API/routers/estudiantes.py
from fastapi import APIRouter, HTTPException, status
from services.estudiante_service import (
    EstudianteService, EstudianteNoEncontradoException, CursoNoEncontradoException
)

router = APIRouter(tags=["Estudiantes"])
servicio = EstudianteService()

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
