# API/routers/auth.py
from fastapi import APIRouter, HTTPException, status

from API.schemas.auth import LoginRequest, LoginRespuesta
from API.services.auth_service import AuthService, CredencialesInvalidasException

router = APIRouter(tags=["Autenticación"])
servicio = AuthService()


@router.post("/api/login", response_model=LoginRespuesta, summary="Inicio de sesión con correo y contraseña")
def login(datos: LoginRequest):
    try:
        return servicio.iniciar_sesion(datos.email, datos.password)
    except CredencialesInvalidasException as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
