"""Módulo Seguridad · ADAPTADOR DE SALIDA: implementa RepositorioUsuarios con SQLite."""
from typing import Optional

from app.compartido.db import conexion
from app.seguridad.dominio import Rol, Usuario
from app.seguridad.puertos import RepositorioUsuarios


def _a_usuario(fila) -> Usuario:
    return Usuario(id=fila["id"], nombre=fila["nombre"], usuario=fila["usuario"], rol=Rol(fila["rol"]))


class RepositorioUsuariosSQLite(RepositorioUsuarios):
    def buscar_con_clave(self, usuario: str) -> Optional[tuple[Usuario, str]]:
        with conexion() as conn:
            fila = conn.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
        return (_a_usuario(fila), fila["clave_hash"]) if fila else None

    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        with conexion() as conn:
            fila = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _a_usuario(fila) if fila else None

    def listar_por_rol(self, rol: Rol) -> list[Usuario]:
        with conexion() as conn:
            filas = conn.execute(
                "SELECT * FROM usuarios WHERE rol = ? ORDER BY nombre", (rol.value,)
            ).fetchall()
        return [_a_usuario(f) for f in filas]
