"""Módulo Motor de Riesgo · ADAPTADOR DE ENTRADA API REST (HU-04 + HU-07).

El estado de riesgo solo lo ve el profesor jefe del curso (restricción de no estigmatizar).
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app import contenedor
from app.seguridad.adaptadores.entrada_api import con_rol
from app.seguridad.dominio import Rol, Usuario

router = APIRouter(prefix="/api", tags=["Motor de Riesgo"])


class AlumnoRiesgo(BaseModel):
    id: int
    nombre: str
    promedio: Optional[float]
    asistencia: Optional[float]
    riesgo: Literal["Bajo", "Medio", "Alto", "Sin datos"]
    semaforo: Literal["Verde", "Amarillo", "Rojo", "Gris"]
    motivo: str


class CursoRiesgo(BaseModel):
    curso_id: int
    curso: str
    conteo: dict[str, int]
    alumnos: list[AlumnoRiesgo]


@router.get("/cursos/{curso_id}/riesgo", response_model=CursoRiesgo, responses={
    401: {"description": "Falta el token o no es válido"},
    403: {"description": "No es el profesor jefe de este curso"}, 404: {"description": "El curso no existe"}})
def riesgo_del_curso(curso_id: int, orden: Literal["riesgo", "nombre", "promedio", "asistencia"] = "riesgo",
                     usuario: Usuario = Depends(con_rol(Rol.PROFESOR))):
    """Lista del curso con promedio, % de asistencia y estado de riesgo (semáforo)."""
    curso = contenedor.acceder_curso.ejecutar(usuario, curso_id)
    filas = contenedor.consultar_riesgo.ejecutar(curso_id, orden)
    return CursoRiesgo(
        curso_id=curso.id, curso=curso.nombre,
        conteo=contenedor.consultar_riesgo.conteo_por_estado(filas),
        alumnos=[AlumnoRiesgo(id=f.id, nombre=f.nombre, promedio=f.promedio, asistencia=f.asistencia,
                              riesgo=f.riesgo, semaforo=f.semaforo, motivo=f.motivo) for f in filas],
    )
