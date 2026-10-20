"""Módulo Seguridad y Usuarios · DOMINIO.

Solo Python estándar: no importa FastAPI ni la base de datos.
"""
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from enum import Enum

ITERACIONES = 100_000
LARGO_MINIMO_CLAVE = 6


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


# ---------- HU-11: registrar usuarios ----------

ROLES_REGISTRABLES = (Rol.ALUMNO, Rol.PROFESOR)


def validar_nuevo_usuario(nombre: str, usuario: str, clave: str, rol: str) -> dict:
    """Revisa los datos del formulario. Devuelve {campo: error}; vacío si todo está bien."""
    errores = {}
    if not (nombre or "").strip():
        errores["nombre"] = "Escriba el nombre completo"
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", (usuario or "").strip()):
        errores["usuario"] = "Use de 3 a 30 letras, números, punto, guion o guion bajo, sin espacios ni tildes"
    if len(clave or "") < LARGO_MINIMO_CLAVE:
        errores["clave"] = f"La contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres"
    if rol not in {r.value for r in ROLES_REGISTRABLES}:
        errores["rol"] = "El rol debe ser alumno o profesor"
    return errores
