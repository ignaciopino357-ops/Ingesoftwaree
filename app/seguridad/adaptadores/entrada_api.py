"""Módulo Seguridad · ADAPTADOR DE ENTRADA API: login con JWT y control de acceso por rol (RF01)."""
from typing import Literal

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


class UsuarioEntrada(BaseModel):
    nombre: str = Field(examples=["Nora Paz"])
    usuario: str = Field(examples=["npaz"])
    clave: str = Field(description="Mínimo 6 caracteres; se guarda cifrada", examples=["secreto1"])
    rol: Literal["alumno", "profesor"]


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


@router.get("/usuarios", response_model=list[UsuarioSalida], tags=["Usuarios"])
def listar_usuarios(rol: Literal["alumno", "profesor"], usuario: Usuario = Depends(con_rol(Rol.DIRECTIVA))):
    """HU-11: usuarios registrados de un rol."""
    return [UsuarioSalida(id=u.id, nombre=u.nombre, usuario=u.usuario, rol=u.rol)
            for u in contenedor.registrar_usuario.listar(Rol(rol))]


@router.post("/usuarios", response_model=UsuarioSalida, status_code=201, tags=["Usuarios"], responses={
    400: {"description": "Datos inválidos (detalle por campo en 'errores')"},
    409: {"description": "El nombre de usuario ya existe"}})
def registrar_usuario(datos: UsuarioEntrada, usuario: Usuario = Depends(con_rol(Rol.DIRECTIVA))):
    """HU-11: la directiva registra un alumno o profesor. Para asignarle curso: POST /api/cursos/{id}/alumnos."""
    nuevo = contenedor.registrar_usuario.ejecutar(datos.nombre, datos.usuario, datos.clave, datos.rol)
    return UsuarioSalida(id=nuevo.id, nombre=nuevo.nombre, usuario=nuevo.usuario, rol=nuevo.rol)
