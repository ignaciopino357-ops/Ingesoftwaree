# Sistema de Detección Temprana y Alerta de Deserción Escolar (Caso 7)

## Descripción
Plataforma web centralizada orientada a la detección precoz y mitigación del riesgo de abandono escolar en educación secundaria y técnico-profesional. Automatiza la ingesta masiva de asistencia y calificaciones, ejecuta un motor analítico en tiempo real y formaliza la derivación psicosocial bajo estricto control de confidencialidad (RBAC).

## Integrantes
- Diego Rubilar
- Mirko Massa
- Constanza Rodríguez
- Ignacio Pino

## Arquitectura
El sistema implementa una **Arquitectura Hexagonal (Ports & Adapters)** estructurada bajo un **Monolito Modular**:
- **Núcleo de Dominio:** Entidades del negocio escolar (Estudiante, EvaluacionRiesgo, Derivacion) y algoritmo de evaluación lógica desacoplado de dependencias externas.
- **Puertos de Aplicación:** Contratos de interfaz para casos de uso (In) y servicios de persistencia/notificación (Out).
- **Adaptadores de Infraestructura:** Controladores REST perimetrales (JWT/RBAC), base de datos relacional y servicios SMTP/PDF.

## Tecnologías
- **Backend Runtime:** Node.js (Express / TypeScript)
- **Base de Datos:** PostgreSQL
- **Seguridad:** Control de Acceso Basado en Roles (RBAC), JWT (JSON Web Tokens) y bcrypt
- **Gestión Ágil:** Taiga (Scrum)
- **Control de Versiones:** Git / GitHub

## Organización del Repositorio
- `docs/`: Artefactos de análisis, especificación de requerimientos y modelado UML de la Unidad I.
- `src/domain/`: Entidades puras y reglas de negocio del motor de detección de riesgo.
- `src/application/`: Casos de uso y contratos de puertos (In/Out).
- `src/infrastructure/`: Adaptadores web REST, controladores de seguridad y adaptadores PostgreSQL/SMTP.
- `tests/`: Pruebas unitarias de casos de uso y cobertura del motor analítico.


##Resumen de base de datos
Tiene 7 tablas y estan basadas en los diagramas UML
use Mysql Workbench para hacer la base de datos
##Tablas:
- Usuario: Guarda a las personas que definimos como usuarios xd y solo acepta esos valores, funciona para poder hacer la HU1

-Cursos: esta tabla depende del usuarioy cada curso tiene su propio ID de profesor jefe y cada profesor puede administrar un solo curso

- Estudiante: esta depende del curso y cada estudiante tiene una ID curso, tienen una columna de riesgo(bajo/medio/alto)

- Registro academico: depende de estudiante y tiene una fila por cada medicion de notas y asistencias en una fecha, tiene varias filas por estudiante en el tiempo lo que nos permitira trabajar en la HU6,HU4 y HU5

-Caso intervencion: depende de estudiante y esta crea una fila ciendo algun profesor deriva a algun estudiante, los estados son(pendiente/en proceso/resuelta) ademas obvservaciones es donde se registra la bitacora

- Mensaje: depende de usuario y guarda las comunicaciones y tiene una ID usuario emisor

- reporte: es independiente y registra datos de cada reporte generado(solo guarda ciando se genero, los filtros y el formato)
