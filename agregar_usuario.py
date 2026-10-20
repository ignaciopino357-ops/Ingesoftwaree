"""Registrar un alumno o profesor desde la consola (script original de Mirko).

Desde el Sprint 3 lo mismo se hace en el portal directiva -> Usuarios (HU-11).
El script usa el mismo caso de uso que el portal, así que aplica las mismas validaciones:
usuario repetido, rol válido y contraseña de al menos 6 caracteres, guardada cifrada.

Uso:  python agregar_usuario.py
"""
from getpass import getpass

from app import contenedor
from app.compartido import db
from app.compartido.errores import ErrorDeNegocio

db.crear_tablas()
usuario = input("Usuario: ").strip()
nombre = input("Nombre completo: ").strip()
rol = input("Rol (alumno/profesor): ").strip().lower()
clave = getpass("Contraseña: ")

try:
    nuevo = contenedor.registrar_usuario.ejecutar(nombre, usuario, clave, rol)
except ErrorDeNegocio as error:
    print(error.mensaje)
    for campo, detalle in error.detalles.items():
        print(f"  - {campo}: {detalle}")
    raise SystemExit(1)

print(f"Usuario {nuevo.usuario} creado correctamente (id {nuevo.id}).")
