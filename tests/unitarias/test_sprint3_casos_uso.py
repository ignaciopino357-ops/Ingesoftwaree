"""Casos de uso del Sprint 3 con repositorios FALSOS en memoria (sin SQLite ni FastAPI)."""
from datetime import date

import pytest

from app.academico.casos_uso import ConsultarMiCalendario, ConsultarMisDatos, PasarLista, RegistrarNotas
from app.academico.puertos import ObservadorCambios
from app.compartido.errores import Conflicto, DatosInvalidos, NoEncontrado, SinPermiso
from app.riesgo.casos_uso import ConsultarCursoConRiesgo, HistorialRiesgo, ResumenRiesgoCursos, VigilarRiesgo
from app.riesgo.puertos import Alerta, FuenteAcademica, RepositorioAlertas
from app.seguridad.casos_uso import RegistrarUsuario
from app.seguridad.dominio import Rol, Usuario, verificar_clave
from app.seguridad.puertos import RepositorioUsuarios
from tests.unitarias.test_casos_uso import (
    DIRECTIVA, PROFE, OTRO_PROFE, AsistenciaFalsa, CalendarioFalso, CursosFalsos, NotasFalsas,
)

ALUMNA = Usuario(10, "Ana", "alumno1", Rol.ALUMNO)
D = date


# ---------- Fuente académica y alertas falsas ----------

class FuenteControlada(FuenteAcademica):
    """Los datos de cada alumno se cambian en la prueba para simular notas y asistencia nuevas."""

    def __init__(self):
        self.datos = {1: {"notas": {"Lenguaje": [6.0]}, "registros": [(D(2026, 9, 1), "P")]}}

    def alumnos(self, curso_id): return [(1, "Emilia")]
    def notas(self, alumno_id): return self.datos[alumno_id]["notas"]
    def conteo_asistencia(self, alumno_id):
        conteo = {"P": 0, "A": 0, "J": 0}
        for _, e in self.datos[alumno_id]["registros"]:
            conteo[e] += 1
        return conteo
    def notas_hasta(self, alumno_id, hasta): return self.datos[alumno_id].get("notas_hasta", {}).get(hasta, self.notas(alumno_id))
    def registros_asistencia(self, alumno_id): return self.datos[alumno_id]["registros"]
    def semestre(self): return D(2026, 9, 1), D(2026, 12, 4)
    def cursos(self): return [(1, "3° Medio A", "Pedro Jara"), (2, "3° Medio B", None)]


class AlertasFalsas(RepositorioAlertas):
    def __init__(self):
        self.guardadas, self.estados = {}, {}

    def crear(self, alumno_id, tipo, clave, motivo, fecha):
        if (alumno_id, tipo, clave) in self.guardadas:
            return False
        self.guardadas[(alumno_id, tipo, clave)] = Alerta(
            len(self.guardadas) + 1, alumno_id, "Emilia", 1, "3° Medio A", PROFE.id, tipo, motivo, fecha, False)
        return True
    def pendientes(self, profesor_id): return [a for a in self.guardadas.values() if a.profesor_id == profesor_id]
    def obtener(self, alerta_id): return next((a for a in self.guardadas.values() if a.id == alerta_id), None)
    def marcar_revisada(self, alerta_id): self.revisada = alerta_id
    def ultimo_estado(self, alumno_id): return self.estados.get(alumno_id)
    def guardar_estado(self, alumno_id, estado): self.estados[alumno_id] = estado


def _poner_en_alto(fuente):
    fuente.datos[1]["notas"] = {"Lenguaje": [3.0]}
    fuente.datos[1]["registros"] = [(D(2026, 9, 1), "P"), (D(2026, 9, 2), "A")]  # 50 %


def _sacar_de_alto(fuente):
    fuente.datos[1]["notas"] = {"Lenguaje": [6.0]}


# ---------- HU-10 ----------

def test_alerta_cuando_pasa_a_alto_y_no_se_repite():
    fuente, alertas = FuenteControlada(), AlertasFalsas()
    vigilar = VigilarRiesgo(fuente, alertas)
    assert vigilar.revisar_curso(1, D(2026, 10, 1)) == 0      # está en Bajo
    _poner_en_alto(fuente)
    assert vigilar.revisar_curso(1, D(2026, 10, 2)) == 1      # entra a Alto
    assert vigilar.revisar_curso(1, D(2026, 10, 5)) == 0      # sigue en Alto: no se repite
    alerta = vigilar.pendientes(PROFE)[0]
    assert alerta.tipo == "riesgo_alto" and "Promedio bajo 4.0" in alerta.motivo


def test_vuelve_a_alertar_si_baja_y_vuelve_a_subir():
    fuente, alertas = FuenteControlada(), AlertasFalsas()
    vigilar = VigilarRiesgo(fuente, alertas)
    _poner_en_alto(fuente)
    vigilar.revisar_curso(1, D(2026, 10, 2))
    _sacar_de_alto(fuente)
    vigilar.revisar_curso(1, D(2026, 10, 5))
    _poner_en_alto(fuente)
    assert vigilar.revisar_curso(1, D(2026, 10, 9)) == 1
    assert len(alertas.guardadas) == 2


def test_solo_el_profesor_jefe_del_curso_revisa_la_alerta():
    fuente, alertas = FuenteControlada(), AlertasFalsas()
    vigilar = VigilarRiesgo(fuente, alertas)
    _poner_en_alto(fuente)
    vigilar.revisar_curso(1, D(2026, 10, 2))
    with pytest.raises(SinPermiso):
        vigilar.marcar_revisada(OTRO_PROFE, 1)
    with pytest.raises(NoEncontrado):
        vigilar.marcar_revisada(PROFE, 99)
    vigilar.marcar_revisada(PROFE, 1)
    assert alertas.revisada == 1


def test_directiva_no_recibe_alertas_con_nombres():
    with pytest.raises(SinPermiso):
        VigilarRiesgo(FuenteControlada(), AlertasFalsas()).pendientes(DIRECTIVA)


# ---------- HU-12 ----------

def test_alerta_por_tres_ausencias_seguidas_una_sola_vez_por_racha():
    fuente, alertas = FuenteControlada(), AlertasFalsas()
    vigilar = VigilarRiesgo(fuente, alertas)
    fuente.datos[1]["registros"] = [(D(2026, 10, d), "P") for d in range(1, 10)] + \
                                   [(D(2026, 10, 13), "A"), (D(2026, 10, 14), "A"), (D(2026, 10, 15), "A")]
    assert vigilar.revisar_curso(1, D(2026, 10, 15)) == 1
    fuente.datos[1]["registros"].append((D(2026, 10, 16), "A"))   # la racha sigue
    assert vigilar.revisar_curso(1, D(2026, 10, 16)) == 0
    alerta = next(a for a in alertas.guardadas.values() if a.tipo == "ausencias")
    assert alerta.motivo == "3 ausencias seguidas: 13-10, 14-10, 15-10"


# ---------- Observador: notas y asistencia avisan al guardar ----------

class ObservadorEspia(ObservadorCambios):
    def __init__(self): self.avisos = []
    def datos_actualizados(self, curso_id, hoy): self.avisos.append((curso_id, hoy))


def test_guardar_notas_y_asistencia_avisa_al_observador():
    espia = ObservadorEspia()
    RegistrarNotas(CursosFalsos(), NotasFalsas(), espia).ejecutar(1, 1, [(10, 1, "5,0")], hoy=D(2026, 10, 13))
    PasarLista(CursosFalsos(), AsistenciaFalsa(), CalendarioFalso(), espia).ejecutar(
        1, D(2026, 10, 13), {}, hoy=D(2026, 10, 13))
    assert espia.avisos == [(1, D(2026, 10, 13)), (1, D(2026, 10, 13))]


def test_si_las_notas_son_invalidas_no_se_avisa():
    espia = ObservadorEspia()
    with pytest.raises(DatosInvalidos):
        RegistrarNotas(CursosFalsos(), NotasFalsas(), espia).ejecutar(1, 1, [(10, 1, "9")])
    assert espia.avisos == []


# ---------- HU-13 ----------

def test_historial_semanal_muestra_como_empeora():
    fuente = FuenteControlada()
    fuente.datos[1]["registros"] = [(D(2026, 9, 1), "P"), (D(2026, 9, 2), "P"),   # semana 1: 100 %
                                    (D(2026, 9, 8), "A"), (D(2026, 9, 9), "A")]    # semana 2: 50 %
    fuente.datos[1]["notas_hasta"] = {D(2026, 9, 6): {"Lenguaje": [6.0]}, D(2026, 9, 13): {"Lenguaje": [6.0, 1.0]}}
    semanas = HistorialRiesgo(fuente).ejecutar(1, hoy=D(2026, 9, 10))
    assert [(s.asistencia, s.promedio, s.riesgo) for s in semanas] == [(100.0, 6.0, "Bajo"), (50.0, 3.5, "Alto")]


def test_semana_sin_datos():
    fuente = FuenteControlada()
    fuente.datos[1]["registros"] = []
    fuente.datos[1]["notas_hasta"] = {D(2026, 9, 6): {}}
    assert HistorialRiesgo(fuente).ejecutar(1, hoy=D(2026, 9, 2))[0].riesgo == "Sin datos"


# ---------- HU-14 ----------

def test_filtrar_por_color():
    from tests.unitarias.test_casos_uso import FuenteFalsa
    filas = ConsultarCursoConRiesgo(FuenteFalsa()).ejecutar(1)
    assert [f.nombre for f in ConsultarCursoConRiesgo.filtrar(filas, ["Alto"])] == ["Emilia"]
    assert len(ConsultarCursoConRiesgo.filtrar(filas, [])) == 2                 # sin filtro: todos
    assert len(ConsultarCursoConRiesgo.filtrar(filas, ["Medio", "Sin datos"])) == 0
    assert len(ConsultarCursoConRiesgo.filtrar(filas, ["Inventado"])) == 2      # valor desconocido se ignora


# ---------- HU-15 ----------

def test_resumen_por_curso_solo_cuenta_sin_nombres():
    fuente = FuenteControlada()
    _poner_en_alto(fuente)
    resumen = ResumenRiesgoCursos(fuente).ejecutar(DIRECTIVA)
    assert resumen["total"]["Alto"] == 2 and resumen["porcentaje_alto"] == 100.0
    assert resumen["cursos"][0]["conteo"] == {"Alto": 1, "Medio": 0, "Bajo": 0, "Sin datos": 0}
    assert "Emilia" not in str(resumen)


def test_resumen_solo_para_directiva():
    with pytest.raises(SinPermiso):
        ResumenRiesgoCursos(FuenteControlada()).ejecutar(PROFE)


# ---------- HU-11 ----------

class UsuariosFalsos(RepositorioUsuarios):
    def __init__(self): self.filas = {"pjara": None}
    def buscar_con_clave(self, usuario): return self.filas.get(usuario)
    def obtener(self, usuario_id): return None
    def listar_por_rol(self, rol): return []
    def existe(self, usuario): return usuario in self.filas
    def crear(self, nombre, usuario, clave_hash, rol):
        self.filas[usuario] = (nombre, clave_hash, rol)
        return 50


def test_registrar_alumno_guarda_la_clave_cifrada():
    repo = UsuariosFalsos()
    nuevo = RegistrarUsuario(repo).ejecutar("  Nora   Paz ", "npaz", "secreto1", "alumno")
    assert nuevo == Usuario(50, "Nora Paz", "npaz", Rol.ALUMNO)
    clave_hash = repo.filas["npaz"][1]
    assert "secreto1" not in clave_hash and verificar_clave("secreto1", clave_hash)


def test_usuario_repetido_es_conflicto():
    with pytest.raises(Conflicto, match="pjara ya existe"):
        RegistrarUsuario(UsuariosFalsos()).ejecutar("Otro Pedro", "pjara", "secreto1", "profesor")


def test_datos_invalidos_no_se_guardan():
    repo = UsuariosFalsos()
    with pytest.raises(DatosInvalidos) as error:
        RegistrarUsuario(repo).ejecutar("", "npaz", "123", "alumno")
    assert set(error.value.detalles) == {"nombre", "clave"}
    assert "npaz" not in repo.filas


# ---------- HU-09 ----------

class NotasDeAna(NotasFalsas):
    def de_alumno(self, alumno_id): return {"Lenguaje": [5.0, 6.0], "Matemática": [3.5]}


class AsistenciaDeAna(AsistenciaFalsa):
    def de_alumno(self, alumno_id):
        return [("2026-10-13", "A"), ("2026-10-09", "J"), ("2026-10-08", "P"), ("2026-10-07", "P")]
    def conteo(self, alumno_id): return {"P": 2, "A": 1, "J": 1}


def test_mis_datos_trae_notas_promedios_y_faltas_sin_riesgo():
    datos = ConsultarMisDatos(CursosFalsos(), NotasDeAna(), AsistenciaDeAna()).ejecutar(ALUMNA)
    assert datos["curso"] == "3° Medio A"
    assert datos["asignaturas"][0] == {"nombre": "Lenguaje", "notas": [5.0, 6.0], "promedio": 5.5}
    assert datos["porcentaje"] == 75.0
    assert datos["ausencias"] == ["2026-10-13"] and datos["justificadas"] == ["2026-10-09"]
    assert not any(clave in datos for clave in ("riesgo", "semaforo", "motivo"))


def test_mis_datos_solo_para_alumnos():
    with pytest.raises(SinPermiso):
        ConsultarMisDatos(CursosFalsos(), NotasDeAna(), AsistenciaDeAna()).ejecutar(PROFE)


# ---------- HU-16 ----------

def _celda(cal, dia):
    return next(c for semana in cal["semanas"] for c in semana if c and c["dia"] == dia)


def test_calendario_pinta_cada_dia_segun_su_estado():
    cal = ConsultarMiCalendario(CalendarioFalso(), AsistenciaDeAna()).ejecutar(ALUMNA, 2026, 10, D(2026, 10, 20))
    assert cal["titulo"] == "Octubre 2026"
    assert _celda(cal, D(2026, 10, 13))["tipo"] == "ausente"
    assert _celda(cal, D(2026, 10, 9))["tipo"] == "justificado"
    assert _celda(cal, D(2026, 10, 8))["tipo"] == "presente"
    assert _celda(cal, D(2026, 10, 14))["tipo"] == "sin-registro"
    feriado = _celda(cal, D(2026, 10, 12))
    assert feriado["tipo"] == "sin-clases" and "Encuentro de Dos Mundos" in feriado["titulo"]
    assert _celda(cal, D(2026, 10, 10))["tipo"] == "sin-clases"   # sábado


def test_navegacion_limitada_al_semestre():
    caso = ConsultarMiCalendario(CalendarioFalso(), AsistenciaDeAna())
    julio = caso.ejecutar(ALUMNA, 2026, 7, D(2026, 10, 20))
    assert julio["anterior"] is None and julio["siguiente"] == (2026, 8)
    fuera = caso.ejecutar(ALUMNA, 2027, 5, D(2026, 10, 20))   # pide un mes fuera: muestra el último
    assert (fuera["anio"], fuera["mes"]) == (2026, 12) and fuera["siguiente"] is None
