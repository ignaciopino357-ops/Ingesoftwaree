"""Módulo Motor de Riesgo · ADAPTADOR DE SALIDA.

Implementa el puerto FuenteAcademica usando los repositorios del módulo de Gestión Académica.
Si mañana las notas vinieran de otro sistema, solo cambia este archivo.
"""
from datetime import date

from app.academico.puertos import RepositorioAsistencia, RepositorioCalendario, RepositorioCursos, RepositorioNotas
from app.riesgo.puertos import FuenteAcademica


class FuenteAcademicaLocal(FuenteAcademica):
    def __init__(self, cursos: RepositorioCursos, notas: RepositorioNotas, asistencia: RepositorioAsistencia,
                 calendario: RepositorioCalendario):
        self.cursos_repo = cursos
        self.notas_repo = notas
        self.asistencia = asistencia
        self.calendario = calendario

    def alumnos(self, curso_id: int) -> list[tuple[int, str]]:
        return [(a.id, a.nombre) for a in self.cursos_repo.alumnos(curso_id)]

    def notas(self, alumno_id: int) -> dict:
        return self.notas_repo.de_alumno(alumno_id)

    def conteo_asistencia(self, alumno_id: int) -> dict:
        return self.asistencia.conteo(alumno_id)

    def notas_hasta(self, alumno_id: int, hasta: date) -> dict:
        return self.notas_repo.de_alumno_hasta(alumno_id, hasta)

    def registros_asistencia(self, alumno_id: int) -> list[tuple[date, str]]:
        return [(date.fromisoformat(f), e) for f, e in self.asistencia.de_alumno(alumno_id)]

    def semestre(self):
        return self.calendario.semestre()

    def cursos(self):
        return [(c.id, c.nombre, c.profesor) for c in self.cursos_repo.listar()]
