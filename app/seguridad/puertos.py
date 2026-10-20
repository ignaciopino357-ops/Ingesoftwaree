"""Módulo Seguridad y Usuarios · PUERTOS DE SALIDA.

Interfaces que el núcleo necesita. Las implementa un adaptador (hoy SQLite).
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.seguridad.dominio import Rol, Usuario


class RepositorioUsuarios(ABC):
    @abstractmethod
    def buscar_con_clave(self, usuario: str) -> Optional[tuple[Usuario, str]]:
        """Devuelve (usuario, hash de la clave) o None si no existe."""

    @abstractmethod
    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        ...

    @abstractmethod
    def listar_por_rol(self, rol: Rol) -> list[Usuario]:
        ...

    @abstractmethod
    def existe(self, usuario: str) -> bool:
        ...

    @abstractmethod
    def crear(self, nombre: str, usuario: str, clave_hash: str, rol: Rol) -> int:
        """Guarda el usuario y devuelve su id (HU-11)."""
