from getpass import getpass

from app.compartido import db
from app.seguridad.dominio import hashear_clave


usuario = input("Usuario: ").strip()
nombre = input("Nombre completo: ").strip()
rol = input("Rol (alumno/profesor): ").strip()
clave = getpass("Contraseña: ")

if rol not in {"alumno", "profesor"}:
    raise ValueError("El rol debe ser alumno o profesor")

with db.conexion() as conn:
    conn.execute(
        """
        INSERT INTO usuarios (nombre, usuario, clave_hash, rol)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, usuario, hashear_clave(clave), rol),
    )

print("Usuario creado correctamente.")