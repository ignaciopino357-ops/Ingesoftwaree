"""Módulo Motor de Riesgo · ADAPTADOR DE SALIDA.

Implementa el puerto FuenteAcademica usando los repositorios del módulo de Gestión Académica.
Si mañana las notas vinieran de otro sistema, solo cambia este archivo.
"""
from app.academico.puertos import RepositorioAsistencia, RepositorioCursos, RepositorioNotas
from app.riesgo.puertos import FuenteAcademica


class FuenteAcademicaLocal(FuenteAcademica):
    def __init__(self, cursos: RepositorioCursos, notas: RepositorioNotas, asistencia: RepositorioAsistencia):
        self.cursos = cursos
        self.notas_repo = notas
        self.asistencia = asistencia

    def alumnos(self, curso_id: int) -> list[tuple[int, str]]:
        return [(a.id, a.nombre) for a in self.cursos.alumnos(curso_id)]

    def notas(self, alumno_id: int) -> dict:
        return self.notas_repo.de_alumno(alumno_id)

    def conteo_asistencia(self, alumno_id: int) -> dict:
        return self.asistencia.conteo(alumno_id)
