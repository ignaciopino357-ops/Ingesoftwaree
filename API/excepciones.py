# API/excepciones.py
# Excepciones de dominio compartidas por los servicios (los routers las traducen a HTTP).


class EstudianteNoEncontradoException(Exception):
    pass


class CursoNoEncontradoException(Exception):
    pass


class EstudianteDuplicadoException(Exception):
    """RUT o correo ya registrados."""
    pass
