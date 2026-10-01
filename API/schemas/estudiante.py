# API/schemas/estudiante.py
from pydantic import BaseModel, Field


class NuevoEstudiante(BaseModel):
    rut: str = Field(min_length=8, max_length=12)
    nombres: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    id_curso: int = Field(gt=0)
