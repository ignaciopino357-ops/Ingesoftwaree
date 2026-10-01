# API/schemas/carga.py
from pydantic import BaseModel
from typing import List, Optional

class FilaError(BaseModel):
    fila: int
    motivo: str

class ResultadoCarga(BaseModel):
    exito: bool
    filas_procesadas: int
    filas_insertadas: int
    filas_con_error: int
    errores: List[FilaError]

class EstadisticasCursoRespuesta(BaseModel):
    exito: bool
    curso: dict
    promedio_notas_curso: Optional[float] = None
    porcentaje_asistencia_curso: Optional[float] = None
    total_estudiantes: int
    total_registros: int
