"""Módulo Gestión Académica · ADAPTADOR DE ENTRADA WEB: portal de la directiva (Controlador del MVC).

HU-02 asignar alumnos y profesor jefe · HU-03 calendario del semestre
"""
from datetime import date

from fastapi import APIRouter, Request

from app import contenedor
from app.academico.dominio import NOMBRES_MES
from app.compartido.errores import ErrorDeNegocio, NoEncontrado
from app.seguridad.adaptadores.entrada_web import usuario_web
from app.seguridad.dominio import Rol
from app.web.vistas import avisar, ir_a, render

router = APIRouter(prefix="/directiva", include_in_schema=False)


def _directiva(request: Request):
    return usuario_web(request, Rol.DIRECTIVA)


def _profesores():
    return contenedor.usuarios.listar_por_rol(Rol.PROFESOR)


def _ejecutar(request: Request, accion, exito: str) -> bool:
    """Ejecuta un caso de uso y deja el mensaje de éxito o de error para la siguiente página."""
    try:
        accion()
    except ErrorDeNegocio as error:
        avisar(request, error.mensaje, "error")
        return False
    avisar(request, exito)
    return True


# ---------- HU-02 ----------

@router.get("")
def portal(request: Request):
    usuario = _directiva(request)
    cursos = [{"id": c.id, "nombre": c.nombre, "profesor": c.profesor,
               "alumnos": len(contenedor.acceder_curso.alumnos(c.id))}
              for c in contenedor.listar_cursos.ejecutar(usuario)]
    sin_curso = sum(1 for _, curso in contenedor.administrar_cursos.todos_los_alumnos() if curso is None)
    return render(request, "directiva/portal.html", cursos=cursos, profesores=_profesores(), sin_curso=sin_curso)


@router.post("/cursos")
async def crear_curso(request: Request):
    _directiva(request)
    form = await request.form()
    nombre = (form.get("nombre") or "").strip()
    resultado = {}

    def crear():
        resultado["id"] = contenedor.administrar_cursos.crear(nombre, form.get("profesor_id") or None)

    if _ejecutar(request, crear, f"Curso {nombre} creado."):
        return ir_a(f"/directiva/cursos/{resultado['id']}")
    return ir_a("/directiva")


@router.get("/cursos/{curso_id}")
def ver_curso(request: Request, curso_id: int):
    usuario = _directiva(request)
    curso = contenedor.acceder_curso.ejecutar(usuario, curso_id, permitir_directiva=True)
    disponibles = [{"id": a.id, "nombre": a.nombre, "curso": nombre_curso}
                   for a, nombre_curso in contenedor.administrar_cursos.todos_los_alumnos()
                   if nombre_curso != curso.nombre]
    return render(request, "directiva/curso.html", curso=curso, alumnos=contenedor.acceder_curso.alumnos(curso_id),
                  disponibles=disponibles, profesores=_profesores())


@router.post("/cursos/{curso_id}/profesor")
async def cambiar_profesor(request: Request, curso_id: int):
    _directiva(request)
    form = await request.form()
    _ejecutar(request, lambda: contenedor.administrar_cursos.asignar_profesor(
        curso_id, form.get("profesor_id") or None), "Profesor jefe actualizado.")
    return ir_a(f"/directiva/cursos/{curso_id}")


@router.post("/cursos/{curso_id}/alumnos")
async def agregar_alumno(request: Request, curso_id: int):
    _directiva(request)
    form = await request.form()
    alumno_id = int(form.get("alumno_id"))
    _ejecutar(request, lambda: contenedor.administrar_cursos.agregar_alumno(curso_id, alumno_id),
              "Alumno agregado al curso.")
    return ir_a(f"/directiva/cursos/{curso_id}")


@router.post("/cursos/{curso_id}/alumnos/{alumno_id}/quitar")
def quitar_alumno(request: Request, curso_id: int, alumno_id: int):
    _directiva(request)
    _ejecutar(request, lambda: contenedor.administrar_cursos.quitar_alumno(curso_id, alumno_id),
              "Alumno quitado del curso. Sus notas y asistencia se conservan.")
    return ir_a(f"/directiva/cursos/{curso_id}")


# ---------- HU-03 ----------

@router.get("/calendario")
def ver_calendario(request: Request, mes: str = ""):
    _directiva(request)
    try:
        anio, num_mes = (int(x) for x in mes.split("-"))
        date(anio, num_mes, 1)
    except ValueError:
        anio, num_mes = date.today().year, date.today().month
    cal = contenedor.administrar_calendario
    inicio, fin = cal.semestre()
    return render(
        request, "directiva/calendario.html", inicio=inicio, fin=fin,
        feriados=sorted(cal.feriados().items()), semanas=cal.mes(anio, num_mes),
        titulo_mes=f"{NOMBRES_MES[num_mes - 1]} {anio}",
        anterior=f"{anio - 1}-12" if num_mes == 1 else f"{anio}-{num_mes - 1:02d}",
        siguiente=f"{anio + 1}-01" if num_mes == 12 else f"{anio}-{num_mes + 1:02d}",
        total_clases=cal.dias_de_clases(),
    )


@router.post("/calendario/semestre")
async def guardar_semestre(request: Request):
    _directiva(request)
    form = await request.form()
    try:
        inicio, fin = date.fromisoformat(form.get("inicio", "")), date.fromisoformat(form.get("fin", ""))
    except ValueError:
        avisar(request, "Ingrese ambas fechas.", "error")
        return ir_a("/directiva/calendario")
    if _ejecutar(request, lambda: contenedor.administrar_calendario.configurar_semestre(inicio, fin),
                 "Semestre guardado."):
        return ir_a(f"/directiva/calendario?mes={inicio.year}-{inicio.month:02d}")
    return ir_a("/directiva/calendario")


@router.post("/calendario/feriados")
async def agregar_feriado(request: Request):
    _directiva(request)
    form = await request.form()
    nombre = (form.get("nombre") or "").strip()
    try:
        dia = date.fromisoformat(form.get("fecha", ""))
    except ValueError:
        avisar(request, "Ingrese la fecha y el nombre del feriado.", "error")
        return ir_a("/directiva/calendario")
    aviso = f"Feriado {nombre} agregado."
    if dia.weekday() >= 5:
        aviso += " Cae en fin de semana, así que no cambia los días de clases."
    _ejecutar(request, lambda: contenedor.administrar_calendario.agregar_feriado(dia, nombre), aviso)
    return ir_a(f"/directiva/calendario?mes={dia.year}-{dia.month:02d}")


@router.post("/calendario/feriados/{fecha}/eliminar")
def eliminar_feriado(request: Request, fecha: str):
    _directiva(request)
    try:
        dia = date.fromisoformat(fecha)
    except ValueError:
        raise NoEncontrado("Feriado no encontrado")
    _ejecutar(request, lambda: contenedor.administrar_calendario.eliminar_feriado(dia), "Feriado eliminado.")
    return ir_a("/directiva/calendario")
