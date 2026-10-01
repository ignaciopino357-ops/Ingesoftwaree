# API/services/estudiante_service.py
import re
import sqlite3
from typing import Dict, List, Optional

from API.database import PASSWORD_INICIAL, hash_password
from API.excepciones import (  # noqa: F401  (se re-exportan para los routers)
    CursoNoEncontradoException,
    EstudianteDuplicadoException,
    EstudianteNoEncontradoException,
)
from API.repositories.curso_repository import CursoRepository
from API.repositories.estudiante_repository import EstudianteRepository


def _promedio(valores: List[float]) -> Optional[float]:
    return round(sum(valores) / len(valores), 1) if valores else None


class EstudianteService:
    def __init__(self, repositorio=None, repositorio_cursos=None):
        self.repositorio = repositorio or EstudianteRepository()
        self.repositorio_cursos = repositorio_cursos or CursoRepository()

    def obtener_portal_estudiante(self, estudiante_id: int):
        datos = self.repositorio.obtener_por_id(estudiante_id)
        if not datos:
            raise EstudianteNoEncontradoException(f"El estudiante con ID {estudiante_id} no existe.")

        regs = datos["registros"]
        notas = [r["nota"] for r in regs if r["nota"] is not None]
        asis = [r["asistencia"] for r in regs if r["asistencia"] is not None]

        # Notas agrupadas por asignatura (las de carga masiva no tienen asignatura -> "General")
        por_asignatura: Dict[str, List[float]] = {}
        for r in regs:
            if r["nota"] is not None:
                por_asignatura.setdefault(r["asignatura"] or "General", []).append(r["nota"])
        asignaturas = {
            nombre: {"notas": lista, "promedio": _promedio(lista)}
            for nombre, lista in por_asignatura.items()
        }

        e = datos["estudiante"]
        promedio = _promedio(notas)
        return {
            "exito": True,
            "id": e["id"], "nombres": e["nombres"], "apellidos": e["apellidos"],
            "rut": e["rut"], "nivel_riesgo_actual": e["nivel_riesgo_actual"],
            "curso": datos["curso"],
            "promedio_general": promedio,
            "promedio_notas": promedio,
            "promedio_asistencia": _promedio(asis),
            "asignaturas": asignaturas,
            "registros": regs,
        }

    def listar_alumnos_ejemplo(self):
        return self.repositorio.listar_alumnos_ejemplo()

    def obtener_curso_con_estudiantes(self, curso_id: int):
        datos = self.repositorio.obtener_por_curso(curso_id)
        if not datos:
            raise CursoNoEncontradoException(f"El curso con ID {curso_id} no existe.")
        return {"exito": True, "curso": datos["curso"], "estudiantes": datos["estudiantes"]}

    def crear_estudiante(self, rut: str, nombres: str, apellidos: str, email: str, id_curso: int):
        rut, email = rut.strip(), email.strip().lower()
        if not self.repositorio_cursos.existe_curso(id_curso):
            raise CursoNoEncontradoException(f"El curso {id_curso} no existe.")
        if self.repositorio.existe_rut(rut):
            raise EstudianteDuplicadoException("Ya existe un alumno con ese RUT.")
        if self.repositorio.existe_email(email):
            raise EstudianteDuplicadoException("Ya existe una cuenta con ese correo.")
        try:
            nuevo_id = self.repositorio.crear(
                rut, nombres.strip(), apellidos.strip(), email, hash_password(PASSWORD_INICIAL), id_curso
            )
        except sqlite3.IntegrityError:  # carrera entre dos altas simultáneas
            raise EstudianteDuplicadoException("Ya existe un alumno con ese RUT o correo.")
        return {"exito": True, "id": nuevo_id,
                "mensaje": f"Alumno creado. Contraseña inicial: {PASSWORD_INICIAL}"}
