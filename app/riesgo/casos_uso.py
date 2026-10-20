"""Módulo Motor de Riesgo · CASOS DE USO.

HU-04 + HU-07: lista del curso con promedio, asistencia y estado de riesgo.
HU-10 + HU-12: alertas al profesor jefe · HU-13: historial semanal · HU-14: filtro por color
HU-15: resumen de riesgo por curso para la directiva (sin nombres).

El riesgo se calcula en el momento con los datos guardados, así que siempre está al día
después de ingresar notas o pasar lista (cálculo síncrono, sin bus de eventos).
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.compartido.errores import NoEncontrado, SinPermiso
from app.riesgo import dominio
from app.riesgo.dominio import ORDEN_RIESGO, calcular_riesgo, porcentaje_asistencia, promedio_general
from app.riesgo.puertos import Alerta, FuenteAcademica, RepositorioAlertas
from app.seguridad.dominio import Rol, Usuario

ESTADOS = ("Alto", "Medio", "Bajo", "Sin datos")


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


def _conteo(registros: list) -> dict:
    conteo = {"P": 0, "A": 0, "J": 0}
    for _, estado in registros:
        conteo[estado] += 1
    return conteo


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
        conteo = {estado: 0 for estado in ESTADOS}
        for fila in filas:
            conteo[fila.riesgo] += 1
        return conteo

    @staticmethod
    def filtrar(filas: list[ResumenAlumno], estados: list[str]) -> list[ResumenAlumno]:
        """HU-14: deja solo los estados elegidos. Lista vacía = sin filtro (todos)."""
        validos = [e for e in estados if e in ESTADOS]
        return [f for f in filas if f.riesgo in validos] if validos else filas


# ---------- HU-10 y HU-12: alertas ----------

class VigilarRiesgo:
    """Revisa un curso después de cada cambio de notas o asistencia y crea las alertas que correspondan."""

    def __init__(self, fuente: FuenteAcademica, alertas: RepositorioAlertas):
        self.fuente = fuente
        self.alertas = alertas
        self.riesgo = ConsultarCursoConRiesgo(fuente)

    def revisar_curso(self, curso_id: int, hoy: date) -> int:
        """Devuelve cuántas alertas nuevas se crearon."""
        nuevas = 0
        for alumno_id, nombre in self.fuente.alumnos(curso_id):
            nuevas += self._riesgo_alto(alumno_id, nombre, hoy)
            nuevas += self._ausencias(alumno_id, hoy)
        return nuevas

    def _riesgo_alto(self, alumno_id: int, nombre: str, hoy: date) -> int:
        actual = self.riesgo.alumno(alumno_id, nombre)
        anterior = self.alertas.ultimo_estado(alumno_id)
        creada = False
        if dominio.debe_alertar_alto(anterior, actual.riesgo):
            # clave = día en que entró a Alto: si baja y vuelve a subir otro día, es otra alerta
            creada = self.alertas.crear(alumno_id, "riesgo_alto", hoy.isoformat(), actual.motivo, hoy)
        if anterior != actual.riesgo:
            self.alertas.guardar_estado(alumno_id, actual.riesgo)
        return int(creada)

    def _ausencias(self, alumno_id: int, hoy: date) -> int:
        creadas = 0
        for racha in dominio.rachas_de_ausencias(self.fuente.registros_asistencia(alumno_id)):
            fechas = ", ".join(d.strftime("%d-%m") for d in racha)
            # clave = primer día de la racha: si la racha sigue creciendo, no se repite la alerta
            if self.alertas.crear(alumno_id, "ausencias", racha[0].isoformat(),
                                  f"{len(racha)} ausencias seguidas: {fechas}", hoy):
                creadas += 1
        return creadas

    def pendientes(self, profesor: Usuario) -> list[Alerta]:
        if profesor.rol != Rol.PROFESOR:
            raise SinPermiso("Las alertas son solo para el profesor jefe")
        return self.alertas.pendientes(profesor.id)

    def marcar_revisada(self, profesor: Usuario, alerta_id: int) -> None:
        alerta = self.alertas.obtener(alerta_id)
        if alerta is None:
            raise NoEncontrado("La alerta no existe")
        if profesor.rol != Rol.PROFESOR or alerta.profesor_id != profesor.id:
            raise SinPermiso("Solo el profesor jefe del curso puede revisar esta alerta")
        self.alertas.marcar_revisada(alerta_id)


# ---------- HU-13: historial semanal ----------

@dataclass(frozen=True)
class SemanaRiesgo:
    lunes: date
    domingo: date
    asistencia: Optional[float]
    promedio: Optional[float]
    riesgo: str
    semaforo: str


class HistorialRiesgo:
    def __init__(self, fuente: FuenteAcademica):
        self.fuente = fuente

    def ejecutar(self, alumno_id: int, hoy: date) -> list[SemanaRiesgo]:
        """Riesgo acumulado al cierre de cada semana del semestre, hasta la semana actual."""
        inicio, fin = self.fuente.semestre()
        registros = self.fuente.registros_asistencia(alumno_id)
        if inicio is None:  # sin semestre configurado: desde el primer registro
            inicio = min((d for d, _ in registros), default=hoy)
        hasta = min(hoy, fin) if fin else hoy
        semanas = []
        for lunes, domingo in dominio.semanas_entre(inicio, hasta):
            conteo = _conteo([r for r in registros if r[0] <= domingo])
            asistencia = porcentaje_asistencia(conteo["P"], conteo["A"], conteo["J"])
            promedio = promedio_general(self.fuente.notas_hasta(alumno_id, domingo))
            evaluacion = calcular_riesgo(asistencia, promedio)
            semanas.append(SemanaRiesgo(lunes, domingo, asistencia, promedio,
                                        evaluacion.estado, evaluacion.semaforo))
        return semanas


# ---------- HU-15: resumen por curso para la directiva ----------

class ResumenRiesgoCursos:
    """Cuenta alumnos por estado en cada curso. No devuelve nombres, notas ni asistencia individual."""

    def __init__(self, fuente: FuenteAcademica):
        self.fuente = fuente
        self.riesgo = ConsultarCursoConRiesgo(fuente)

    def ejecutar(self, usuario: Usuario) -> dict:
        if usuario.rol != Rol.DIRECTIVA:
            raise SinPermiso("No tiene acceso a esta sección")
        cursos, total = [], {estado: 0 for estado in ESTADOS}
        for curso_id, nombre, profesor in self.fuente.cursos():
            conteo = self.riesgo.conteo_por_estado(self.riesgo.ejecutar(curso_id))
            for estado, n in conteo.items():
                total[estado] += n
            cursos.append({"id": curso_id, "nombre": nombre, "profesor": profesor,
                           "conteo": conteo, "alumnos": sum(conteo.values())})
        alumnos = sum(total.values())
        return {"cursos": cursos, "total": total, "alumnos": alumnos,
                "porcentaje_alto": round(total["Alto"] * 100 / alumnos, 1) if alumnos else None}
