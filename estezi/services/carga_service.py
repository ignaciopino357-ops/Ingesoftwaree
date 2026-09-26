# API/services/carga_service.py
# Tarea 3 (Back): parser de Excel/CSV con validación de tipos de datos.
# Reglas: nota entre 1.0 y 7.0, asistencia entre 0 y 100, id_estudiante debe existir.
#
# Formato esperado del archivo (encabezados exactos, en cualquier orden):
#   id_estudiante | fecha | nota | asistencia
# fecha en formato AAAA-MM-DD.

import csv
import io
from datetime import datetime
from openpyxl import load_workbook
from database import obtener_conexion

COLUMNAS_OBLIGATORIAS = {"id_estudiante", "fecha", "nota", "asistencia"}


class ArchivoInvalidoException(Exception):
    """Extensión no soportada o encabezados incorrectos: se rechaza antes de procesar."""
    pass


class CargaService:

    # ---------- Lectura de archivo -> filas crudas (dict por fila) ----------
    def leer_archivo(self, nombre_archivo: str, contenido: bytes):
        extension = nombre_archivo.lower().rsplit(".", 1)[-1] if "." in nombre_archivo else ""
        if extension == "csv":
            return self._leer_csv(contenido)
        if extension in ("xlsx", "xlsm"):
            return self._leer_excel(contenido)
        raise ArchivoInvalidoException(
            f"Extensión '.{extension}' no soportada. Solo se aceptan .csv y .xlsx."
        )

    def _leer_csv(self, contenido: bytes):
        texto = contenido.decode("utf-8-sig")
        lector = csv.DictReader(io.StringIO(texto))
        self._validar_encabezados(lector.fieldnames)
        return list(lector)

    def _leer_excel(self, contenido: bytes):
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
        hoja = libro.active
        filas_crudas = list(hoja.iter_rows(values_only=True))
        if not filas_crudas:
            raise ArchivoInvalidoException("El archivo Excel está vacío.")
        encabezados = [str(c).strip() if c is not None else "" for c in filas_crudas[0]]
        self._validar_encabezados(encabezados)
        filas = []
        for fila in filas_crudas[1:]:
            if all(v is None for v in fila):
                continue  # ignora filas vacías al final del archivo
            filas.append({encabezados[i]: fila[i] for i in range(len(encabezados))})
        return filas

    def _validar_encabezados(self, encabezados):
        if not encabezados or not COLUMNAS_OBLIGATORIAS.issubset(set(encabezados)):
            faltantes = COLUMNAS_OBLIGATORIAS - set(encabezados or [])
            raise ArchivoInvalidoException(
                f"Faltan columnas obligatorias: {', '.join(sorted(faltantes))}."
            )

    # ---------- Validación fila por fila ----------
    def _validar_fila(self, fila: dict, ids_validos: set):
        """Retorna (dict_limpio, None) si la fila es válida, o (None, 'motivo') si no."""
        try:
            id_estudiante = int(fila["id_estudiante"])
        except (TypeError, ValueError):
            return None, "id_estudiante no es un número entero"

        if id_estudiante not in ids_validos:
            return None, f"id_estudiante {id_estudiante} no existe en la base de datos"

        fecha_raw = fila.get("fecha")
        try:
            fecha = str(fecha_raw)[:10] if not hasattr(fecha_raw, "strftime") else fecha_raw.strftime("%Y-%m-%d")
            datetime.strptime(fecha, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None, "fecha inválida (formato esperado AAAA-MM-DD)"

        try:
            nota = float(fila["nota"])
        except (TypeError, ValueError):
            return None, "nota no es un número"
        if not (1.0 <= nota <= 7.0):
            return None, f"nota {nota} fuera de rango (debe ser entre 1.0 y 7.0)"

        try:
            asistencia = float(fila["asistencia"])
        except (TypeError, ValueError):
            return None, "asistencia no es un número"
        if not (0.0 <= asistencia <= 100.0):
            return None, f"asistencia {asistencia} fuera de rango (debe ser entre 0 y 100)"

        return {"id_estudiante": id_estudiante, "fecha": fecha, "nota": nota, "asistencia": asistencia}, None

    # ---------- Orquestación: leer + validar + insertar ----------
    def procesar_carga(self, nombre_archivo: str, contenido: bytes) -> dict:
        filas = self.leer_archivo(nombre_archivo, contenido)

        con = obtener_conexion()
        ids_validos = {r["id"] for r in con.execute("SELECT id FROM Estudiante").fetchall()}

        errores = []
        filas_validas = []
        for i, fila in enumerate(filas, start=2):  # fila 2 = primera fila de datos (1 es encabezado)
            limpia, motivo = self._validar_fila(fila, ids_validos)
            if motivo:
                errores.append({"fila": i, "motivo": motivo})
            else:
                filas_validas.append(limpia)

        if filas_validas:
            con.executemany(
                "INSERT INTO RegistroAcademico (id_estudiante, fecha, asistencia, nota) VALUES (?,?,?,?)",
                [(f["id_estudiante"], f["fecha"], f["asistencia"], f["nota"]) for f in filas_validas],
            )
            con.commit()
        con.close()

        return {
            "exito": True,
            "filas_procesadas": len(filas),
            "filas_insertadas": len(filas_validas),
            "filas_con_error": len(errores),
            "errores": errores,
        }
