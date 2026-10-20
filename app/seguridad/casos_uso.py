"""Módulo Seguridad y Usuarios · CASOS DE USO (puertos de entrada).

HU-01: iniciar sesión y control de acceso por rol (RBAC).
HU-11: la directiva registra alumnos y profesores.
"""
from app.compartido.errores import Conflicto, DatosInvalidos, NoAutenticado, SinPermiso
from app.seguridad.dominio import Rol, Usuario, hashear_clave, validar_nuevo_usuario, verificar_clave
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


class RegistrarUsuario:
    """HU-11: crea un alumno o profesor. La contraseña se guarda cifrada con PBKDF2."""

    def __init__(self, usuarios: RepositorioUsuarios):
        self.usuarios = usuarios

    def ejecutar(self, nombre: str, usuario: str, clave: str, rol: str) -> Usuario:
        errores = validar_nuevo_usuario(nombre, usuario, clave, rol)
        if errores:
            raise DatosInvalidos("No se guardó: revise los campos marcados.", errores)
        usuario, nombre = usuario.strip(), " ".join(nombre.split())
        if self.usuarios.existe(usuario):
            raise Conflicto(f"No se guardó: el usuario {usuario} ya existe. Elija otro.", {"usuario": "Ya existe"})
        nuevo_id = self.usuarios.crear(nombre, usuario, hashear_clave(clave), Rol(rol))
        return Usuario(nuevo_id, nombre, usuario, Rol(rol))

    def listar(self, rol: Rol) -> list[Usuario]:
        return self.usuarios.listar_por_rol(rol)
