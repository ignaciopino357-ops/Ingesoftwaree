"""Módulo Seguridad y Usuarios · CASOS DE USO (puertos de entrada).

HU-01: iniciar sesión y control de acceso por rol (RBAC).
"""
from app.compartido.errores import NoAutenticado, SinPermiso
from app.seguridad.dominio import Rol, Usuario, verificar_clave
from app.seguridad.puertos import RepositorioUsuarios


class IniciarSesion:
    def __init__(self, usuarios: RepositorioUsuarios):
        self.usuarios = usuarios

    def ejecutar(self, usuario: str, clave: str) -> Usuario:
        encontrado = self.usuarios.buscar_con_clave(usuario.strip())
        if encontrado is None or not verificar_clave(clave, encontrado[1]):
            raise NoAutenticado("Usuario o contraseña incorrectos")
        return encontrado[0]


class ObtenerUsuario:
    def __init__(self, usuarios: RepositorioUsuarios):
        self.usuarios = usuarios

    def ejecutar(self, usuario_id: int) -> Usuario:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NoAutenticado("La sesión ya no es válida")
        return usuario


def exigir_rol(usuario: Usuario, *roles: Rol) -> Usuario:
    """RBAC: deja pasar solo a los roles indicados (HU-01, criterio 3)."""
    if usuario.rol not in roles:
        raise SinPermiso("No tiene acceso a esta sección")
    return usuario
