# Sistema de Detección Temprana y Alerta de Deserción Escolar (Caso 7)

## Descripción
Plataforma web centralizada orientada a la detección precoz y mitigación del riesgo de abandono escolar en educación secundaria y técnico-profesional. Automatiza la ingesta masiva de asistencia y calificaciones, ejecuta un motor analítico en tiempo real y formaliza la derivación psicosocial bajo estricto control de confidencialidad (RBAC).

## Integrantes
- Diego Rubilar
- Mirko Massa
- Constanza Rodríguez
- Ignacio Pino

## Arquitectura
API REST en **Python / FastAPI** organizada en capas dentro de un monolito modular:
- **routers/**: adaptadores de entrada HTTP (validan la petición y traducen excepciones a códigos HTTP).
- **services/**: reglas de negocio (login, carga académica, carga masiva de notas, reportes).
- **repositories/**: acceso a datos (SQL sobre SQLite).
- **schemas/**: modelos Pydantic de entrada/salida.
- **frontend/**: portal web (HTML + JS) servido por la propia API en `/app/`.

## Tecnologías
- **Backend:** Python 3.10+ · FastAPI · Uvicorn
- **Base de datos:** SQLite (archivo `API/sprint1.db`, se crea sola al arrancar con datos de prueba)
- **Excel/CSV:** openpyxl + csv
- **Seguridad:** contraseñas con PBKDF2-HMAC-SHA256 + sal. *Pendiente:* JWT y control de acceso por rol (RBAC) en los endpoints.
- **Gestión ágil:** Taiga (Scrum) · **Versiones:** Git / GitHub

## Cómo ejecutar
```bash
pip install -r requirements.txt
uvicorn main:app --reload        # ejecutar SIEMPRE desde la carpeta raíz del proyecto
```
- Portal: http://127.0.0.1:8000/app/
- Documentación interactiva: http://127.0.0.1:8000/docs
- Tests: `pytest`
- Cuentas de prueba (contraseña `123456`): `diego.docente@liceo.cl`, `mirko.jefe@liceo.cl`, `ana.soto@alumno.liceo.cl`

## Organización del Repositorio
- `main.py`: punto de entrada de la aplicación.
- `API/`: código del backend (routers, services, repositories, schemas, database).
- `frontend/`: páginas del portal.
- `docs/`: artefactos de análisis, requerimientos y UML.
- `tests/`: pruebas automáticas (usan una base de datos temporal).
- `BaseDatos.sql`: script MySQL de referencia del diseño (el código actual usa SQLite; ver `API/database.py`).

## Resumen de base de datos
Tiene 7 tablas y estan basadas en los diagramas UML
use Mysql Workbench para hacer la base de datos
##Tablas:
- Usuario: Guarda a las personas que definimos como usuarios xd y solo acepta esos valores, funciona para poder hacer la HU1

- Cursos: esta tabla depende del usuarioy cada curso tiene su propio ID de profesor jefe y cada profesor puede administrar un solo curso

- Estudiante: esta depende del curso y cada estudiante tiene una ID curso, tienen una columna de riesgo(bajo/medio/alto)

- Registro academico: depende de estudiante y tiene una fila por cada medicion de notas y asistencias en una fecha, tiene varias filas por estudiante en el tiempo lo que nos permitira trabajar en la HU6,HU4 y HU5

-Caso intervencion: depende de estudiante y esta crea una fila ciendo algun profesor deriva a algun estudiante, los estados son(pendiente/en proceso/resuelta) ademas obvservaciones es donde se registra la bitacora

- Mensaje: depende de usuario y guarda las comunicaciones y tiene una ID usuario emisor

- reporte: es independiente y registra datos de cada reporte generado(solo guarda ciando se genero, los filtros y el formato)
