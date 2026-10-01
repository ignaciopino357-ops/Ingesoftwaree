# API/services/auth_service.py
from API.database import conexion_bd, verificar_password


class CredencialesInvalidasException(Exception):
    pass


class AuthService:
    # Mensaje único: no revela si el correo existe o no (evita enumeración de cuentas).
    MENSAJE = "Correo o contraseña incorrectos."

    def iniciar_sesion(self, email: str, password: str) -> dict:
        email = email.strip().lower()
        with conexion_bd() as con:
            docente = con.execute(
                "SELECT * FROM Usuario WHERE lower(email) = ? AND activo = 1", (email,)
            ).fetchone()
            alumno = None if docente else con.execute(
                "SELECT * FROM Estudiante WHERE lower(email) = ?", (email,)
            ).fetchone()

        if docente and verificar_password(password, docente["password_hash"]):
            return {"exito": True, "tipo": "DOCENTE", "id": docente["id"],
                    "nombre": docente["nombre_completo"], "rol": docente["rol"]}

        if alumno and verificar_password(password, alumno["password_hash"]):
            return {"exito": True, "tipo": "ESTUDIANTE", "id": alumno["id"],
                    "nombre": f'{alumno["nombres"]} {alumno["apellidos"]}', "rol": None}

        raise CredencialesInvalidasException(self.MENSAJE)
