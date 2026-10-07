"""Pruebas unitarias de Seguridad: contraseñas, JWT y RBAC (HU-01)."""
import pytest

from app.compartido.errores import NoAutenticado, SinPermiso
from app.seguridad.adaptadores.token_jwt import MINUTOS_VALIDEZ, crear_token, leer_token
from app.seguridad.casos_uso import exigir_rol
from app.seguridad.dominio import Rol, Usuario, hashear_clave, verificar_clave


def test_clave_hasheada_se_verifica_y_no_se_guarda_en_texto_plano():
    clave_hash = hashear_clave("profe123")
    assert "profe123" not in clave_hash
    assert verificar_clave("profe123", clave_hash)
    assert not verificar_clave("otra", clave_hash)


def test_token_valido_devuelve_usuario_y_rol():
    datos = leer_token(crear_token(7, "profesor", ahora=1000), ahora=1000)
    assert datos["sub"] == "7" and datos["rol"] == "profesor"


def test_token_expira_a_los_60_minutos():
    token = crear_token(7, "profesor", ahora=0)
    leer_token(token, ahora=MINUTOS_VALIDEZ * 60 - 1)  # todavía vale
    with pytest.raises(NoAutenticado, match="expirado"):
        leer_token(token, ahora=MINUTOS_VALIDEZ * 60 + 1)


def test_token_alterado_es_rechazado():
    cabecera, datos, firma = crear_token(7, "profesor").split(".")
    with pytest.raises(NoAutenticado):
        leer_token(f"{cabecera}.{datos}.{firma[:-2]}xx")


def test_rbac_bloquea_otro_rol():
    alumno = Usuario(5, "Ana", "alumno1", Rol.ALUMNO)
    assert exigir_rol(alumno, Rol.ALUMNO) is alumno
    with pytest.raises(SinPermiso):
        exigir_rol(alumno, Rol.PROFESOR, Rol.DIRECTIVA)
