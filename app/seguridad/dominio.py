"""Módulo Seguridad y Usuarios · DOMINIO.

Solo Python estándar: no importa FastAPI ni la base de datos.
"""
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from enum import Enum

ITERACIONES = 100_000


class Rol(str, Enum):
    DIRECTIVA = "directiva"
    PROFESOR = "profesor"
    ALUMNO = "alumno"


PORTAL_POR_ROL = {
    Rol.DIRECTIVA: "/directiva",
    Rol.PROFESOR: "/profesor",
    Rol.ALUMNO: "/alumno",
}

NOMBRE_ROL = {
    Rol.DIRECTIVA: "Directiva",
    Rol.PROFESOR: "Profesor jefe",
    Rol.ALUMNO: "Alumno",
}


@dataclass(frozen=True)
class Usuario:
    id: int
    nombre: str
    usuario: str
    rol: Rol

    @property
    def portal(self) -> str:
        return PORTAL_POR_ROL[self.rol]


def hashear_clave(clave: str) -> str:
    """PBKDF2-HMAC-SHA256 con sal aleatoria (RNF01)."""
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), ITERACIONES).hex()
    return f"{sal}${digest}"


def verificar_clave(clave: str, clave_hash: str) -> bool:
    sal, digest = clave_hash.split("$", 1)
    calculado = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), ITERACIONES).hex()
    return hmac.compare_digest(calculado, digest)
