"""Módulo Seguridad · ADAPTADOR DE ENTRADA API: login con JWT y control de acceso por rol (RF01)."""
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app import contenedor
from app.compartido.errores import NoAutenticado
from app.seguridad.adaptadores.token_jwt import MINUTOS_VALIDEZ, crear_token, leer_token
from app.seguridad.casos_uso import exigir_rol
from app.seguridad.dominio import Rol, Usuario

router = APIRouter(prefix="/api", tags=["Seguridad"])
bearer = HTTPBearer(auto_error=False)


class LoginEntrada(BaseModel):
    usuario: str = Field(min_length=1, examples=["pjara"])
    clave: str = Field(min_length=1, examples=["profe123"])


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_minutos: int
    rol: Rol
    nombre: str


class UsuarioSalida(BaseModel):
    id: int
    nombre: str
    usuario: str
    rol: Rol


def usuario_api(credenciales: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Usuario:
    """Lee el token Bearer. Sin token o con token inválido -> 401."""
    if credenciales is None:
        raise NoAutenticado("Falta el token. Use POST /api/login y envíe 'Authorization: Bearer <token>'")
    datos = leer_token(credenciales.credentials)
    return contenedor.obtener_usuario.ejecutar(int(datos["sub"]))


def con_rol(*roles: Rol):
    """Dependencia RBAC: solo deja pasar a los roles indicados (403 si no)."""
    def dependencia(usuario: Usuario = Depends(usuario_api)) -> Usuario:
        return exigir_rol(usuario, *roles)
    return dependencia


@router.post("/login", response_model=TokenSalida, responses={401: {"description": "Credenciales incorrectas"}})
def login(datos: LoginEntrada):
    """HU-01: entrega un token JWT válido por 60 minutos."""
    usuario = contenedor.iniciar_sesion.ejecutar(datos.usuario, datos.clave)
    return TokenSalida(access_token=crear_token(usuario.id, usuario.rol.value),
                       expira_en_minutos=MINUTOS_VALIDEZ, rol=usuario.rol, nombre=usuario.nombre)


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: Usuario = Depends(usuario_api)):
    """Datos del usuario dueño del token."""
    return UsuarioSalida(id=usuario.id, nombre=usuario.nombre, usuario=usuario.usuario, rol=usuario.rol)
