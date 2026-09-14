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