from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginRespuesta(BaseModel):
    exito: bool
    tipo: str          # "DOCENTE" o "ESTUDIANTE"
    id: int
    nombre: str
    rol: str | None = None
