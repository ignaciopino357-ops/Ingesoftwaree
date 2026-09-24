# API/schemas/curso.py
# Modelos Pydantic para validación y serialización de Cursos (Punto 10.21)

from pydantic import BaseModel, Field
from typing import List, Optional

class CursoRespuesta(BaseModel):
    """Esquema de salida individual para un curso asignado."""
    id: int
    nombre: str = Field(..., description="Nombre del curso, ej: 1° Medio A")
    nivel: str = Field(..., description="Nivel educativo")
    letra: str = Field(..., min_length=1, max_length=1, description="Sección o letra")
    anio_lectivo: int = Field(..., description="Año escolar correspondiente")
    id_profesor_jefe: Optional[int] = Field(None, description="ID del docente asignado")
    total_estudiantes: int = Field(default=0, ge=0, description="Total de alumnos matriculados")

    class Config:
        from_attributes = True

class ConsultaCursosRespuesta(BaseModel):
    """Esquema de respuesta envolvente para el endpoint de HU 1 (CU-01)."""
    exito: bool
    tiene_carga: bool
    mensaje: Optional[str] = None
    total_cursos: int
    cursos: List[CursoRespuesta]