"""Módulo Motor de Riesgo · PUERTOS DE SALIDA.

El motor no lee la base de datos: pide los datos académicos a través de FuenteAcademica.
La implementa un adaptador que conversa con el módulo de Gestión Académica
(dependencia Motor de Riesgo -> Gestión Académica, como define el Hito 1).
Las alertas se guardan a través de RepositorioAlertas.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


class FuenteAcademica(ABC):
    @abstractmethod
    def alumnos(self, curso_id: int) -> list[tuple[int, str]]:
        """[(alumno_id, nombre)]"""

    @abstractmethod
    def notas(self, alumno_id: int) -> dict:
        """{asignatura: [notas]}"""

    @abstractmethod
    def conteo_asistencia(self, alumno_id: int) -> dict:
        """{"P": n, "A": n, "J": n}"""

    @abstractmethod
    def notas_hasta(self, alumno_id: int, hasta: date) -> dict:
        """Notas ingresadas hasta esa fecha (HU-13)."""

    @abstractmethod
    def registros_asistencia(self, alumno_id: int) -> list[tuple[date, str]]:
        """[(fecha, estado)] de los días con lista pasada (HU-12 y HU-13)."""

    @abstractmethod
    def semestre(self) -> tuple[Optional[date], Optional[date]]: ...

    @abstractmethod
    def cursos(self) -> list[tuple[int, str, Optional[str]]]:
        """[(curso_id, nombre, profesor jefe)] (HU-15)."""


@dataclass(frozen=True)
class Alerta:
    id: int
    alumno_id: int
    alumno: str
    curso_id: Optional[int]
    curso: Optional[str]
    profesor_id: Optional[int]
    tipo: str          # "riesgo_alto" o "ausencias"
    motivo: str
    fecha: date
    revisada: bool

    @property
    def titulo(self) -> str:
        return {"riesgo_alto": "Pasó a riesgo Alto", "ausencias": "3 ausencias seguidas"}[self.tipo]


class RepositorioAlertas(ABC):
    @abstractmethod
    def crear(self, alumno_id: int, tipo: str, clave: str, motivo: str, fecha: date) -> bool:
        """Guarda la alerta. Devuelve False si ya existía una con el mismo (alumno, tipo, clave)."""

    @abstractmethod
    def pendientes(self, profesor_id: int) -> list[Alerta]:
        """Alertas sin revisar de los alumnos de los cursos de ese profesor jefe, la más nueva primero."""

    @abstractmethod
    def obtener(self, alerta_id: int) -> Optional[Alerta]: ...

    @abstractmethod
    def marcar_revisada(self, alerta_id: int) -> None: ...

    @abstractmethod
    def ultimo_estado(self, alumno_id: int) -> Optional[str]: ...

    @abstractmethod
    def guardar_estado(self, alumno_id: int, estado: str) -> None: ...
