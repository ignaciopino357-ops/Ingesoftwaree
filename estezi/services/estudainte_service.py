# API/services/estudiante_service.py
from repositories.estudiante_repository import EstudianteRepository

class EstudianteNoEncontradoException(Exception):
    pass

class CursoNoEncontradoException(Exception):
    pass

class EstudianteService:
    def __init__(self, repositorio=None):
        self.repositorio = repositorio or EstudianteRepository()

    def obtener_portal_estudiante(self, estudiante_id: int):
        datos = self.repositorio.obtener_por_id(estudiante_id)
        if not datos:
            raise EstudianteNoEncontradoException(f"El estudiante con ID {estudiante_id} no existe.")
        regs = datos["registros"]
        notas = [r["nota"] for r in regs if r["nota"] is not None]
        asis = [r["asistencia"] for r in regs if r["asistencia"] is not None]
        e = datos["estudiante"]
        return {
            "exito": True,
            "id": e["id"], "nombres": e["nombres"], "apellidos": e["apellidos"],
            "rut": e["rut"], "nivel_riesgo_actual": e["nivel_riesgo_actual"],
            "curso": datos["curso"],
            "promedio_notas": round(sum(notas) / len(notas), 1) if notas else None,
            "promedio_asistencia": round(sum(asis) / len(asis), 1) if asis else None,
            "registros": regs,
        }

    def listar_alumnos_ejemplo(self):
        return self.repositorio.listar_alumnos_ejemplo()

    def obtener_curso_con_estudiantes(self, curso_id: int):
        datos = self.repositorio.obtener_por_curso(curso_id)
        if not datos:
            raise CursoNoEncontradoException(f"El curso con ID {curso_id} no existe.")
        return {"exito": True, "curso": datos["curso"], "estudiantes": datos["estudiantes"]}
