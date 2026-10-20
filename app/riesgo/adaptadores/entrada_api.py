"""Módulo Motor de Riesgo · ADAPTADOR DE ENTRADA API REST.

HU-04 + HU-07 riesgo del curso · HU-10/HU-12 alertas · HU-13 historial · HU-14 filtro · HU-15 resumen.
El estado de riesgo con nombres solo lo ve el profesor jefe del curso (restricción de no estigmatizar);
la directiva solo ve conteos por curso.
"""
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app import contenedor
from app.compartido.errores import NoEncontrado
from app.seguridad.adaptadores.entrada_api import con_rol
from app.seguridad.dominio import Rol, Usuario

router = APIRouter(prefix="/api", tags=["Motor de Riesgo"])
solo_profesor = con_rol(Rol.PROFESOR)
EstadoRiesgo = Literal["Bajo", "Medio", "Alto", "Sin datos"]
ERRORES = {401: {"description": "Falta el token o no es válido"}, 403: {"description": "Rol o curso no autorizado"},
           404: {"description": "No existe"}}


class AlumnoRiesgo(BaseModel):
    id: int
    nombre: str
    promedio: Optional[float]
    asistencia: Optional[float]
    riesgo: EstadoRiesgo
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
                     estado: list[EstadoRiesgo] = Query(default=[], description="HU-14: filtrar por uno o varios estados"),
                     usuario: Usuario = Depends(solo_profesor)):
    """Lista del curso con promedio, % de asistencia y estado de riesgo (semáforo).

    El conteo siempre es del curso completo, aunque se filtre por estado.
    """
    curso = contenedor.acceder_curso.ejecutar(usuario, curso_id)
    filas = contenedor.consultar_riesgo.ejecutar(curso_id, orden)
    return CursoRiesgo(
        curso_id=curso.id, curso=curso.nombre,
        conteo=contenedor.consultar_riesgo.conteo_por_estado(filas),
        alumnos=[AlumnoRiesgo(id=f.id, nombre=f.nombre, promedio=f.promedio, asistencia=f.asistencia,
                              riesgo=f.riesgo, semaforo=f.semaforo, motivo=f.motivo)
                 for f in contenedor.consultar_riesgo.filtrar(filas, estado)],
    )


# ---------- HU-10 y HU-12: alertas ----------

class AlertaSalida(BaseModel):
    id: int
    alumno_id: int
    alumno: str
    curso_id: Optional[int]
    curso: Optional[str]
    tipo: Literal["riesgo_alto", "ausencias"]
    titulo: str
    motivo: str
    fecha: date


class Mensaje(BaseModel):
    mensaje: str


@router.get("/alertas", response_model=list[AlertaSalida], responses=ERRORES)
def alertas_pendientes(usuario: Usuario = Depends(solo_profesor)):
    """Alertas sin revisar de los alumnos de mis cursos, la más nueva primero."""
    return [AlertaSalida(id=a.id, alumno_id=a.alumno_id, alumno=a.alumno, curso_id=a.curso_id, curso=a.curso,
                         tipo=a.tipo, titulo=a.titulo, motivo=a.motivo, fecha=a.fecha)
            for a in contenedor.vigilar_riesgo.pendientes(usuario)]


@router.post("/alertas/{alerta_id}/revisada", response_model=Mensaje, responses=ERRORES)
def marcar_alerta_revisada(alerta_id: int, usuario: Usuario = Depends(solo_profesor)):
    contenedor.vigilar_riesgo.marcar_revisada(usuario, alerta_id)
    return Mensaje(mensaje="Alerta marcada como revisada.")


# ---------- HU-13: historial ----------

class SemanaSalida(BaseModel):
    lunes: date
    domingo: date
    asistencia: Optional[float]
    promedio: Optional[float]
    riesgo: EstadoRiesgo


@router.get("/cursos/{curso_id}/alumnos/{alumno_id}/historial", response_model=list[SemanaSalida],
            responses=ERRORES)
def historial(curso_id: int, alumno_id: int, usuario: Usuario = Depends(solo_profesor)):
    """Riesgo acumulado al cierre de cada semana del semestre."""
    contenedor.acceder_curso.ejecutar(usuario, curso_id)
    if alumno_id not in {a.id for a in contenedor.acceder_curso.alumnos(curso_id)}:
        raise NoEncontrado("El alumno no pertenece a este curso")
    return [SemanaSalida(lunes=s.lunes, domingo=s.domingo, asistencia=s.asistencia, promedio=s.promedio,
                         riesgo=s.riesgo) for s in contenedor.historial_riesgo.ejecutar(alumno_id, date.today())]


# ---------- HU-15: resumen para la directiva ----------

class CursoResumen(BaseModel):
    id: int
    nombre: str
    profesor: Optional[str]
    alumnos: int
    conteo: dict[str, int]


class ResumenSalida(BaseModel):
    alumnos: int
    total: dict[str, int]
    porcentaje_alto: Optional[float]
    cursos: list[CursoResumen]


@router.get("/riesgo/resumen", response_model=ResumenSalida, responses=ERRORES)
def resumen_por_curso(usuario: Usuario = Depends(con_rol(Rol.DIRECTIVA))):
    """Cantidad de alumnos por estado de riesgo en cada curso. Sin nombres ni datos individuales."""
    return ResumenSalida(**contenedor.resumen_riesgo.ejecutar(usuario))
