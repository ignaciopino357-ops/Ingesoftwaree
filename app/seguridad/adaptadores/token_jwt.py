"""Módulo Seguridad · ADAPTADOR: tokens JWT (HS256) para la API REST.

Implementado con la librería estándar (hmac + base64) para no agregar dependencias.
RF01: el token expira a los 60 minutos.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from app.compartido.errores import NoAutenticado

CLAVE = os.environ.get("SECRET_KEY", "cambiar-en-produccion").encode()
MINUTOS_VALIDEZ = 60


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _desde_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firmar(contenido: str) -> str:
    return _b64(hmac.new(CLAVE, contenido.encode(), hashlib.sha256).digest())


def crear_token(usuario_id: int, rol: str, ahora: float | None = None) -> str:
    ahora = time.time() if ahora is None else ahora
    cabecera = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    datos = _b64(json.dumps({"sub": str(usuario_id), "rol": rol, "exp": int(ahora) + MINUTOS_VALIDEZ * 60}).encode())
    return f"{cabecera}.{datos}.{_firmar(f'{cabecera}.{datos}')}"


def leer_token(token: str, ahora: float | None = None) -> dict:
    """Devuelve el contenido del token o lanza NoAutenticado si es inválido o expiró."""
    try:
        cabecera, datos, firma = token.split(".")
        if not hmac.compare_digest(firma, _firmar(f"{cabecera}.{datos}")):
            raise ValueError("firma")
        contenido = json.loads(_desde_b64(datos))
    except ValueError:
        raise NoAutenticado("Token inválido")
    if contenido["exp"] < (time.time() if ahora is None else ahora):
        raise NoAutenticado("Token expirado: inicie sesión de nuevo")
    return contenido
