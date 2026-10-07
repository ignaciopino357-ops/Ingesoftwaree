"""Módulo Motor de Riesgo · CASOS DE USO.

HU-04 + HU-07: lista del curso con promedio, asistencia y estado de riesgo.
El riesgo se calcula en el momento con los datos guardados, así que siempre está al día
después de ingresar notas o pasar lista (cálculo síncrono, sin bus de eventos).
"""
from dataclasses import dataclass
from typing import Optional

from app.riesgo.dominio import ORDEN_RIESGO, calcular_riesgo, porcentaje_asistencia, promedio_general
from app.riesgo.puertos import FuenteAcademica


@dataclass(frozen=True)
class ResumenAlumno:
    id: int
    nombre: str
    promedio: Optional[float]
    asistencia: Optional[float]
    riesgo: str
    semaforo: str
    motivo: str
    conteo: dict


ORDENES = {
    "riesgo": lambda a: (ORDEN_RIESGO[a.riesgo], a.nombre),
    "nombre": lambda a: a.nombre,
    "promedio": lambda a: (a.promedio is None, a.promedio or 0),
    "asistencia": lambda a: (a.asistencia is None, a.asistencia or 0),
}


class ConsultarCursoConRiesgo:
    def __init__(self, fuente: FuenteAcademica):
        self.fuente = fuente

    def alumno(self, alumno_id: int, nombre: str) -> ResumenAlumno:
        conteo = self.fuente.conteo_asistencia(alumno_id)
        asistencia = porcentaje_asistencia(conteo["P"], conteo["A"], conteo["J"])
        promedio = promedio_general(self.fuente.notas(alumno_id))
        evaluacion = calcular_riesgo(asistencia, promedio)
        return ResumenAlumno(alumno_id, nombre, promedio, asistencia,
                             evaluacion.estado, evaluacion.semaforo, evaluacion.motivo, conteo)

    def ejecutar(self, curso_id: int, orden: str = "riesgo") -> list[ResumenAlumno]:
        filas = [self.alumno(alumno_id, nombre) for alumno_id, nombre in self.fuente.alumnos(curso_id)]
        return sorted(filas, key=ORDENES.get(orden, ORDENES["riesgo"]))

    @staticmethod
    def conteo_por_estado(filas: list[ResumenAlumno]) -> dict:
        conteo = {estado: 0 for estado in ("Alto", "Medio", "Bajo", "Sin datos")}
        for fila in filas:
            conteo[fila.riesgo] += 1
        return conteo
