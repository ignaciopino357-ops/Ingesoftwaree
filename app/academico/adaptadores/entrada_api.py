"""Módulo Gestión Académica · ADAPTADOR DE ENTRADA API REST (JSON, documentado en /docs).

Los modelos Pydantic son los DTO (el "Modelo" del MVC). Los errores de negocio
se convierten en códigos HTTP en app/main.py: 400, 401, 403, 404 y 409.
"""
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from app import contenedor
from app.compartido.errores import NoEncontrado
from app.seguridad.adaptadores.entrada_api import con_rol
from app.seguridad.dominio import Rol, Usuario

router = APIRouter(prefix="/api", tags=["Gestión Académica"])
solo_profesor = con_rol(Rol.PROFESOR)
solo_directiva = con_rol(Rol.DIRECTIVA)
profesor_o_directiva = con_rol(Rol.PROFESOR, Rol.DIRECTIVA)
ERRORES = {401: {"description": "Falta el token o no es válido"}, 403: {"description": "Rol o curso no autorizado"},
           404: {"description": "No existe"}}


# ---------- DTO ----------

class CursoSalida(BaseModel):
    id: int
    nombre: str
    profesor_id: Optional[int]
    profesor: Optional[str]


class AlumnoSalida(BaseModel):
    id: int
    nombre: str


class NotaEntrada(BaseModel):
    alumno_id: int
    numero: int = Field(description="Evaluación de 1 a 6")
    nota: Optional[float] = Field(description="1.0 a 7.0; null para borrar")


class NotasEntrada(BaseModel):
    asignatura_id: int
    notas: list[NotaEntrada]


class AsistenciaEntrada(BaseModel):
    fecha: date
    registros: dict[int, Literal["P", "A", "J"]] = Field(
        description="{alumno_id: estado}. Quien no aparece queda Presente", examples=[{"5": "P", "9": "A"}])


class CursoEntrada(BaseModel):
    nombre: str = Field(min_length=1, examples=["4° Medio A"])
    profesor_id: Optional[int] = None


class ProfesorEntrada(BaseModel):
    profesor_id: Optional[int]


class AlumnoEntrada(BaseModel):
    alumno_id: int


class SemestreEntrada(BaseModel):
    inicio: date
    fin: date


class FeriadoEntrada(BaseModel):
    fecha: date
    nombre: str = Field(min_length=1, examples=["Fiestas Patrias"])


class Mensaje(BaseModel):
    mensaje: str


def _curso(usuario: Usuario, curso_id: int, permitir_directiva: bool = False):
    return contenedor.acceder_curso.ejecutar(usuario, curso_id, permitir_directiva)


# ---------- Cursos (HU-01 / HU-04) ----------

@router.get("/cursos", response_model=list[CursoSalida], responses=ERRORES)
def listar_cursos(usuario: Usuario = Depends(profesor_o_directiva)):
    """Profesor jefe: sus cursos. Directiva: todos."""
    return [CursoSalida(**c.__dict__) for c in contenedor.listar_cursos.ejecutar(usuario)]


@router.get("/cursos/{curso_id}/alumnos", response_model=list[AlumnoSalida], responses=ERRORES)
def alumnos_del_curso(curso_id: int, usuario: Usuario = Depends(profesor_o_directiva)):
    _curso(usuario, curso_id, permitir_directiva=True)
    return [AlumnoSalida(id=a.id, nombre=a.nombre) for a in contenedor.acceder_curso.alumnos(curso_id)]


# ---------- HU-05: notas ----------

@router.get("/cursos/{curso_id}/notas", responses=ERRORES)
def ver_notas(curso_id: int, asignatura_id: int, usuario: Usuario = Depends(solo_profesor)):
    """Notas de una asignatura: {alumno_id: {numero: nota}}."""
    _curso(usuario, curso_id)
    return contenedor.consultar_notas.de_asignatura(curso_id, asignatura_id)


@router.put("/cursos/{curso_id}/notas", response_model=Mensaje,
            responses={**ERRORES, 400: {"description": "Alguna nota fuera de 1.0–7.0; no se guarda ninguna"}})
def registrar_notas(curso_id: int, datos: NotasEntrada, usuario: Usuario = Depends(solo_profesor)):
    """HU-05: guarda varias notas en una sola transacción. Si una es inválida, no se guarda nada."""
    _curso(usuario, curso_id)
    guardadas = contenedor.registrar_notas.ejecutar(
        curso_id, datos.asignatura_id, [(n.alumno_id, n.numero, n.nota) for n in datos.notas])
    return Mensaje(mensaje=f"{guardadas} nota(s) guardada(s). Riesgo actualizado.")


# ---------- HU-06: asistencia ----------

@router.get("/cursos/{curso_id}/asistencia", responses=ERRORES)
def ver_asistencia(curso_id: int, fecha: date, usuario: Usuario = Depends(solo_profesor)):
    _curso(usuario, curso_id)
    return {"fecha": fecha, "bloqueo": contenedor.pasar_lista.bloqueo(fecha, date.today()),
            "registros": contenedor.pasar_lista.consultar(curso_id, fecha)}


@router.put("/cursos/{curso_id}/asistencia", response_model=Mensaje,
            responses={**ERRORES, 400: {"description": "Fin de semana, feriado, fuera del semestre o día futuro"}})
def pasar_lista(curso_id: int, datos: AsistenciaEntrada, usuario: Usuario = Depends(solo_profesor)):
    """HU-06: registra Presente (P), Ausente (A) o Justificado (J) para un día de clases."""
    _curso(usuario, curso_id)
    total = contenedor.pasar_lista.ejecutar(curso_id, datos.fecha, datos.registros, hoy=date.today())
    return Mensaje(mensaje=f"Asistencia de {total} alumno(s) guardada.")


# ---------- HU-08: exportar ----------

@router.get("/cursos/{curso_id}/exportar/{tipo}", responses={
    **ERRORES, 200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}})
def exportar(curso_id: int, tipo: Literal["notas", "asistencia"], usuario: Usuario = Depends(solo_profesor)):
    """HU-08: descarga un .xlsx. 404 si el curso no tiene datos."""
    _curso(usuario, curso_id)
    generar = contenedor.exportar_curso.notas_excel if tipo == "notas" else contenedor.exportar_curso.asistencia_excel
    return Response(generar(curso_id),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{tipo}_curso_{curso_id}.xlsx"'})


# ---------- HU-02: administración de cursos (directiva) ----------

@router.post("/cursos", response_model=CursoSalida, status_code=201,
             responses={**ERRORES, 409: {"description": "Ya existe un curso con ese nombre"}})
def crear_curso(datos: CursoEntrada, usuario: Usuario = Depends(solo_directiva)):
    curso_id = contenedor.administrar_cursos.crear(datos.nombre, datos.profesor_id)
    return CursoSalida(**contenedor.acceder_curso.ejecutar(usuario, curso_id, True).__dict__)


@router.put("/cursos/{curso_id}/profesor", response_model=Mensaje, responses=ERRORES)
def asignar_profesor(curso_id: int, datos: ProfesorEntrada, usuario: Usuario = Depends(solo_directiva)):
    contenedor.administrar_cursos.asignar_profesor(curso_id, datos.profesor_id)
    return Mensaje(mensaje="Profesor jefe actualizado.")


@router.post("/cursos/{curso_id}/alumnos", response_model=Mensaje, status_code=201,
             responses={**ERRORES, 409: {"description": "El alumno ya pertenece a otro curso"}})
def agregar_alumno(curso_id: int, datos: AlumnoEntrada, usuario: Usuario = Depends(solo_directiva)):
    contenedor.administrar_cursos.agregar_alumno(curso_id, datos.alumno_id)
    return Mensaje(mensaje="Alumno agregado al curso.")


@router.delete("/cursos/{curso_id}/alumnos/{alumno_id}", status_code=204, responses=ERRORES)
def quitar_alumno(curso_id: int, alumno_id: int, usuario: Usuario = Depends(solo_directiva)):
    contenedor.administrar_cursos.quitar_alumno(curso_id, alumno_id)
    return Response(status_code=204)


# ---------- HU-03: calendario (directiva) ----------

@router.get("/calendario", tags=["Calendario"])
def ver_calendario(usuario: Usuario = Depends(profesor_o_directiva)):
    cal = contenedor.administrar_calendario
    inicio, fin = cal.semestre()
    return {"inicio": inicio, "fin": fin, "dias_de_clases": cal.dias_de_clases(),
            "feriados": [{"fecha": f, "nombre": n} for f, n in sorted(cal.feriados().items())]}


@router.put("/calendario/semestre", response_model=Mensaje, tags=["Calendario"],
            responses={**ERRORES, 400: {"description": "El término es anterior al inicio"}})
def configurar_semestre(datos: SemestreEntrada, usuario: Usuario = Depends(solo_directiva)):
    contenedor.administrar_calendario.configurar_semestre(datos.inicio, datos.fin)
    return Mensaje(mensaje="Semestre guardado.")


@router.post("/calendario/feriados", response_model=Mensaje, status_code=201, tags=["Calendario"], responses=ERRORES)
def agregar_feriado(datos: FeriadoEntrada, usuario: Usuario = Depends(solo_directiva)):
    contenedor.administrar_calendario.agregar_feriado(datos.fecha, datos.nombre)
    return Mensaje(mensaje=f"Feriado {datos.nombre} agregado.")


@router.delete("/calendario/feriados/{fecha}", status_code=204, tags=["Calendario"], responses=ERRORES)
def eliminar_feriado(fecha: date, usuario: Usuario = Depends(solo_directiva)):
    if fecha not in contenedor.administrar_calendario.feriados():
        raise NoEncontrado("Ese día no es feriado")
    contenedor.administrar_calendario.eliminar_feriado(fecha)
    return Response(status_code=204)
