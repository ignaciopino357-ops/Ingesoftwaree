"""HU-01: contraseñas, sesión y control de acceso por rol."""
import hashlib
import hmac
import secrets
from typing import Optional

from fastapi import HTTPException, Request

from app.db import conexion

PORTAL_POR_ROL = {
    "directiva": "/directiva",
    "profesor": "/profesor",
    "alumno": "/alumno",
}


class NoAutenticado(Exception):
    """Se lanza cuando alguien sin sesión entra a una página protegida."""


def hashear_clave(clave: str) -> str:
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), 100_000).hex()
    return f"{sal}${digest}"


def verificar_clave(clave: str, clave_hash: str) -> bool:
    sal, digest = clave_hash.split("$", 1)
    calculado = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), 100_000).hex()
    return hmac.compare_digest(calculado, digest)


def autenticar(usuario: str, clave: str) -> Optional[dict]:
    with conexion() as conn:
        fila = conn.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario.strip(),)).fetchone()
    if fila and verificar_clave(clave, fila["clave_hash"]):
        return dict(fila)
    return None


def usuario_actual(request: Request) -> Optional[dict]:
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return None
    with conexion() as conn:
        fila = conn.execute(
            "SELECT id, nombre, usuario, rol FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
    return dict(fila) if fila else None


def exigir_rol(request: Request, rol: str) -> dict:
    """Devuelve el usuario si tiene el rol pedido.

    - Sin sesión: lo manda al login.
    - Con otro rol: 403 "No tiene acceso a esta sección" (HU-01, criterio 3).
    """
    usuario = usuario_actual(request)
    if usuario is None:
        raise NoAutenticado()
    if usuario["rol"] != rol:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta sección")
    return usuario
