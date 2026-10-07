"""HU-01: iniciar sesión y llegar al portal según rol."""
from fastapi import APIRouter, Request

from app.auth import PORTAL_POR_ROL, autenticar, usuario_actual
from app.web import ir_a, render

router = APIRouter()


@router.get("/")
def inicio(request: Request):
    usuario = usuario_actual(request)
    if usuario:
        return ir_a(PORTAL_POR_ROL[usuario["rol"]])
    return ir_a("/login")


@router.get("/login")
def ver_login(request: Request):
    return render(request, "login.html", usuario=None)


@router.post("/login")
async def hacer_login(request: Request):
    form = await request.form()
    usuario = autenticar(form.get("usuario", ""), form.get("clave", ""))
    if usuario is None:
        return render(
            request, "login.html", status_code=401, usuario=None,
            error="Usuario o contraseña incorrectos", usuario_escrito=form.get("usuario", ""),
        )
    request.session.clear()
    request.session["usuario_id"] = usuario["id"]
    return ir_a(PORTAL_POR_ROL[usuario["rol"]])


@router.post("/logout")
def cerrar_sesion(request: Request):
    request.session.clear()
    return ir_a("/login")
