"""Módulo Seguridad · ADAPTADOR DE ENTRADA WEB: login con formulario y sesión firmada (HU-01)."""
from typing import Optional

from fastapi import APIRouter, Request

from app import contenedor
from app.compartido.errores import NoAutenticado
from app.seguridad.casos_uso import exigir_rol
from app.seguridad.dominio import Rol, Usuario
from app.web.vistas import ir_a, render

router = APIRouter(tags=["Web"], include_in_schema=False)


def usuario_en_sesion(request: Request) -> Optional[Usuario]:
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return None
    try:
        return contenedor.obtener_usuario.ejecutar(usuario_id)
    except NoAutenticado:
        request.session.clear()
        return None


def usuario_web(request: Request, *roles: Rol) -> Usuario:
    """Sin sesión -> NoAutenticado (va al login). Con otro rol -> SinPermiso (403)."""
    usuario = usuario_en_sesion(request)
    if usuario is None:
        raise NoAutenticado("Inicie sesión")
    return exigir_rol(usuario, *roles)


@router.get("/")
def inicio(request: Request):
    usuario = usuario_en_sesion(request)
    return ir_a(usuario.portal if usuario else "/login")


@router.get("/login")
def ver_login(request: Request):
    return render(request, "login.html", usuario=None)


@router.post("/login")
async def hacer_login(request: Request):
    form = await request.form()
    try:
        usuario = contenedor.iniciar_sesion.ejecutar(form.get("usuario", ""), form.get("clave", ""))
    except NoAutenticado as error:
        return render(request, "login.html", status_code=401, usuario=None,
                      error=error.mensaje, usuario_escrito=form.get("usuario", ""))
    request.session.clear()
    request.session["usuario_id"] = usuario.id
    return ir_a(usuario.portal)


@router.post("/logout")
def cerrar_sesion(request: Request):
    request.session.clear()
    return ir_a("/login")
