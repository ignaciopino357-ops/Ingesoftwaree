# API/schemas/estudiante.py
from pydantic import BaseModel
from typing import List, Optional

class RegistroRespuesta(BaseModel):
    fecha: str
    asistencia: Optional[float] = None
    nota: Optional[float] = None

class EstudiantePortalRespuesta(BaseModel):
    exito: bool
    id: int
    nombres: str
    apellidos: str
    rut: str
    nivel_riesgo_actual: str
    curso: dict
    promedio_notas: Optional[float] = None
    promedio_asistencia: Optional[float] = None
    registros: List[RegistroRespuesta]

class EstudianteCursoRespuesta(BaseModel):
    id: int
    nombres: str
    apellidos: str
    rut: str
    nivel_riesgo_actual: str
    promedio_notas: Optional[float] = None
    promedio_asistencia: Optional[float] = None

class CursoConEstudiantesRespuesta(BaseModel):
    exito: bool
    curso: dict
    estudiantes: List[EstudianteCursoRespuesta]
