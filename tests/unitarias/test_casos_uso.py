"""Pruebas de casos de uso con repositorios FALSOS en memoria.

Muestran la ventaja de los puertos: los casos de uso se prueban sin SQLite ni FastAPI,
reemplazando el adaptador real por uno de mentira que cumple la misma interfaz.
"""
from datetime import date

import pytest

from app.academico.casos_uso import AccederCurso, AdministrarCursos, PasarLista, RegistrarNotas
from app.academico.dominio import Alumno, Curso
from app.academico.puertos import RepositorioAsistencia, RepositorioCalendario, RepositorioCursos, RepositorioNotas
from app.compartido.errores import Conflicto, DatosInvalidos, NoEncontrado, SinPermiso
from app.riesgo.casos_uso import ConsultarCursoConRiesgo
from app.riesgo.puertos import FuenteAcademica
from app.seguridad.dominio import Rol, Usuario

PROFE = Usuario(2, "Pedro Jara", "pjara", Rol.PROFESOR)
OTRO_PROFE = Usuario(3, "Carolina Muñoz", "cmunoz", Rol.PROFESOR)
DIRECTIVA = Usuario(1, "María Soto", "directiva", Rol.DIRECTIVA)


class CursosFalsos(RepositorioCursos):
    def __init__(self):
        self.cursos = {1: Curso(1, "3° Medio A", 2, "Pedro Jara")}
        self.miembros = {10: 1, 11: 1}
        self.nombres = {10: "Ana", 11: "Benjamín", 12: "Karla"}

    def obtener(self, curso_id): return self.cursos.get(curso_id)
    def listar(self): return list(self.cursos.values())
    def listar_de_profesor(self, profesor_id): return [c for c in self.cursos.values() if c.profesor_id == profesor_id]
    def existe_nombre(self, nombre): return any(c.nombre == nombre for c in self.cursos.values())
    def crear(self, nombre, profesor_id):
        nuevo = max(self.cursos) + 1
        self.cursos[nuevo] = Curso(nuevo, nombre, profesor_id, None)
        return nuevo
    def asignar_profesor(self, curso_id, profesor_id): pass
    def alumnos(self, curso_id):
        return [Alumno(a, self.nombres[a]) for a, c in self.miembros.items() if c == curso_id]
    def todos_los_alumnos(self):
        return [(Alumno(a, n), self.cursos[self.miembros[a]].nombre if a in self.miembros else None)
                for a, n in self.nombres.items()]
    def curso_de_alumno(self, alumno_id):
        return self.cursos[self.miembros[alumno_id]].nombre if alumno_id in self.miembros else None
    def agregar_alumno(self, curso_id, alumno_id): self.miembros[alumno_id] = curso_id
    def quitar_alumno(self, curso_id, alumno_id): self.miembros.pop(alumno_id, None)


class NotasFalsas(RepositorioNotas):
    def __init__(self): self.guardadas = None
    def asignaturas(self): return [{"id": 1, "nombre": "Lenguaje"}]
    def de_alumno(self, alumno_id): return {}
    def de_asignatura(self, curso_id, asignatura_id): return {}
    def guardar(self, asignatura_id, cambios): self.guardadas = cambios


class AsistenciaFalsa(RepositorioAsistencia):
    def __init__(self): self.guardada = None
    def de_alumno(self, alumno_id): return []
    def conteo(self, alumno_id): return {"P": 0, "A": 0, "J": 0}
    def del_dia(self, curso_id, dia): return {}
    def fechas(self, curso_id): return []
    def guardar(self, dia, estados): self.guardada = (dia, estados)


class CalendarioFalso(RepositorioCalendario):
    def semestre(self): return date(2026, 7, 27), date(2026, 12, 4)
    def guardar_semestre(self, inicio, fin): pass
    def feriados(self): return {date(2026, 10, 12): "Encuentro de Dos Mundos"}
    def guardar_feriado(self, dia, nombre): pass
    def eliminar_feriado(self, dia): pass


# ---------- Acceso (RBAC) ----------

def test_profesor_accede_a_su_curso():
    assert AccederCurso(CursosFalsos()).ejecutar(PROFE, 1).nombre == "3° Medio A"


def test_profesor_no_accede_a_curso_ajeno():
    with pytest.raises(SinPermiso):
        AccederCurso(CursosFalsos()).ejecutar(OTRO_PROFE, 1)


def test_curso_inexistente():
    with pytest.raises(NoEncontrado):
        AccederCurso(CursosFalsos()).ejecutar(PROFE, 99)


# ---------- Notas: todo o nada ----------

def test_una_nota_invalida_impide_guardar_todas():
    # Arrange
    notas = NotasFalsas()
    caso = RegistrarNotas(CursosFalsos(), notas)
    # Act + Assert
    with pytest.raises(DatosInvalidos) as error:
        caso.ejecutar(1, 1, [(10, 1, "6,5"), (11, 1, "9")])
    assert "n_11_1" in error.value.detalles
    assert notas.guardadas is None  # no se guardó ni la nota válida


def test_notas_validas_se_guardan_y_vacio_borra():
    notas = NotasFalsas()
    guardadas = RegistrarNotas(CursosFalsos(), notas).ejecutar(1, 1, [(10, 1, "6,5"), (11, 1, "")])
    assert guardadas == 1
    assert notas.guardadas == [(10, 1, 6.5), (11, 1, None)]


def test_no_se_ponen_notas_a_alumnos_de_otro_curso():
    with pytest.raises(DatosInvalidos):
        RegistrarNotas(CursosFalsos(), NotasFalsas()).ejecutar(1, 1, [(12, 1, "5.0")])


# ---------- Asistencia ----------

def test_pasar_lista_completa_con_presente_por_defecto():
    asistencia = AsistenciaFalsa()
    caso = PasarLista(CursosFalsos(), asistencia, CalendarioFalso())
    caso.ejecutar(1, date(2026, 10, 13), {11: "A"}, hoy=date(2026, 10, 13))
    assert asistencia.guardada == (date(2026, 10, 13), {10: "P", 11: "A"})


def test_no_se_pasa_lista_en_feriado():
    caso = PasarLista(CursosFalsos(), AsistenciaFalsa(), CalendarioFalso())
    with pytest.raises(DatosInvalidos, match="Encuentro de Dos Mundos"):
        caso.ejecutar(1, date(2026, 10, 12), {}, hoy=date(2026, 10, 20))


# ---------- Cursos (HU-02) ----------

def test_alumno_no_puede_estar_en_dos_cursos():
    cursos = CursosFalsos()
    nuevo = AdministrarCursos(cursos).crear("3° Medio B", None)
    with pytest.raises(Conflicto, match="3° Medio A"):
        AdministrarCursos(cursos).agregar_alumno(nuevo, 10)


def test_nombre_de_curso_repetido_es_conflicto():
    with pytest.raises(Conflicto):
        AdministrarCursos(CursosFalsos()).crear("3° Medio A", None)


# ---------- Motor de riesgo con una fuente falsa ----------

class FuenteFalsa(FuenteAcademica):
    def alumnos(self, curso_id): return [(1, "Ana"), (2, "Emilia")]
    def notas(self, alumno_id): return {"Lenguaje": [6.0]} if alumno_id == 1 else {"Lenguaje": [3.0]}
    def conteo_asistencia(self, alumno_id): return {"P": 10, "A": 0, "J": 0} if alumno_id == 1 else {"P": 6, "A": 4, "J": 0}


def test_curso_ordenado_con_mayor_riesgo_primero():
    filas = ConsultarCursoConRiesgo(FuenteFalsa()).ejecutar(1)
    assert [(f.nombre, f.riesgo) for f in filas] == [("Emilia", "Alto"), ("Ana", "Bajo")]
    assert ConsultarCursoConRiesgo.conteo_por_estado(filas)["Alto"] == 1
