"""Módulo Motor de Riesgo · PUERTO DE SALIDA.

El motor no lee la base de datos: pide los datos académicos a través de este puerto.
Lo implementa un adaptador que conversa con el módulo de Gestión Académica
(dependencia Motor de Riesgo -> Gestión Académica, como define el Hito 1).
"""
from abc import ABC, abstractmethod


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
