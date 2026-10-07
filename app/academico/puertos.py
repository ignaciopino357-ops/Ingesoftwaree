"""Módulo Gestión Académica · PUERTOS DE SALIDA.

Lo que el núcleo necesita del exterior. Hoy lo implementan adaptadores SQLite y Excel;
mañana podría ser PostgreSQL sin tocar el dominio ni los casos de uso.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.academico.dominio import Alumno, Curso


class RepositorioCursos(ABC):
    @abstractmethod
    def obtener(self, curso_id: int) -> Optional[Curso]: ...

    @abstractmethod
    def listar(self) -> list[Curso]: ...

    @abstractmethod
    def listar_de_profesor(self, profesor_id: int) -> list[Curso]: ...

    @abstractmethod
    def existe_nombre(self, nombre: str) -> bool: ...

    @abstractmethod
    def crear(self, nombre: str, profesor_id: Optional[int]) -> int: ...

    @abstractmethod
    def asignar_profesor(self, curso_id: int, profesor_id: Optional[int]) -> None: ...

    @abstractmethod
    def alumnos(self, curso_id: int) -> list[Alumno]: ...

    @abstractmethod
    def todos_los_alumnos(self) -> list[tuple[Alumno, Optional[str]]]:
        """Cada alumno con el nombre de su curso (o None)."""

    @abstractmethod
    def curso_de_alumno(self, alumno_id: int) -> Optional[str]: ...

    @abstractmethod
    def agregar_alumno(self, curso_id: int, alumno_id: int) -> None: ...

    @abstractmethod
    def quitar_alumno(self, curso_id: int, alumno_id: int) -> None: ...


class RepositorioNotas(ABC):
    @abstractmethod
    def asignaturas(self) -> list[dict]: ...

    @abstractmethod
    def de_alumno(self, alumno_id: int) -> dict:
        """{nombre_asignatura: [notas en orden]}"""

    @abstractmethod
    def de_asignatura(self, curso_id: int, asignatura_id: int) -> dict:
        """{alumno_id: {numero: nota}}"""

    @abstractmethod
    def guardar(self, asignatura_id: int, cambios: list[tuple[int, int, Optional[float]]]) -> None:
        """Cambios (alumno_id, numero, nota). Nota None = borrar. Todo en una transacción."""


class RepositorioAsistencia(ABC):
    @abstractmethod
    def de_alumno(self, alumno_id: int) -> list[tuple[str, str]]:
        """[(fecha ISO, estado)] del más reciente al más antiguo."""

    @abstractmethod
    def conteo(self, alumno_id: int) -> dict:
        """{"P": n, "A": n, "J": n}"""

    @abstractmethod
    def del_dia(self, curso_id: int, dia: date) -> dict:
        """{alumno_id: estado}"""

    @abstractmethod
    def fechas(self, curso_id: int) -> list[str]: ...

    @abstractmethod
    def guardar(self, dia: date, estados: dict) -> None:
        """{alumno_id: estado} en una transacción."""


class RepositorioCalendario(ABC):
    @abstractmethod
    def semestre(self) -> tuple[Optional[date], Optional[date]]: ...

    @abstractmethod
    def guardar_semestre(self, inicio: date, fin: date) -> None: ...

    @abstractmethod
    def feriados(self) -> dict:
        """{date: nombre}"""

    @abstractmethod
    def guardar_feriado(self, dia: date, nombre: str) -> None: ...

    @abstractmethod
    def eliminar_feriado(self, dia: date) -> None: ...


class ExportadorPlanillas(ABC):
    @abstractmethod
    def notas(self, alumnos: list[Alumno], hojas: list[tuple[str, dict]]) -> bytes:
        """hojas = [(nombre_asignatura, {alumno_id: {numero: nota}})]"""

    @abstractmethod
    def asistencia(self, alumnos: list[Alumno], fechas: list[str], registros: dict, conteos: dict) -> bytes:
        """registros = {alumno_id: {fecha: estado}}, conteos = {alumno_id: {"P","A","J"}}"""
