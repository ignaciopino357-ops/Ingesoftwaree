"""Errores de negocio compartidos por todos los módulos.

Los casos de uso lanzan estos errores sin saber nada de HTTP.
Los adaptadores de entrada los traducen: la API a códigos HTTP y la web a mensajes en pantalla.
"""


class ErrorDeNegocio(Exception):
    codigo_http = 400

    def __init__(self, mensaje: str, detalles: dict | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles or {}


class DatosInvalidos(ErrorDeNegocio):
    """Los datos no cumplen una regla (nota fuera de rango, día sin clases...)."""
    codigo_http = 400


class NoAutenticado(ErrorDeNegocio):
    """No hay sesión, el token no es válido o las credenciales son incorrectas."""
    codigo_http = 401


class SinPermiso(ErrorDeNegocio):
    """El usuario existe pero su rol o su curso no le permiten la operación (RBAC)."""
    codigo_http = 403


class NoEncontrado(ErrorDeNegocio):
    codigo_http = 404


class Conflicto(ErrorDeNegocio):
    """La operación choca con el estado actual (alumno ya asignado a otro curso, nombre repetido...)."""
    codigo_http = 409
