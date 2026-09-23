// src/infrastructure/adapters/out/curso_repository.js
// Adaptador Secundario: Persistencia de Cursos (HU 1 / Tarea #19)
// Basado en el esquema SQL de alerta_desercion_escolar

const Curso = require('../../../domain/models/curso');

class CursoRepository {
    constructor(dbConnection = null) {
        this.db = dbConnection;
    }

    async obtenerPorDocenteId(docenteId) {
        // Si existe pool/conexión activa a MySQL, ejecuta la consulta real
        if (this.db) {
            const query = `
                SELECT 
                    c.id, 
                    c.nombre, 
                    c.nivel, 
                    c.letra, 
                    c.anio_lectivo, 
                    c.id_profesor_jefe,
                    COUNT(e.id) AS total_estudiantes
                FROM Curso c
                LEFT JOIN Estudiante e ON e.id_curso = c.id
                WHERE c.id_profesor_jefe = ?
                GROUP BY c.id, c.nombre, c.nivel, c.letra, c.anio_lectivo, c.id_profesor_jefe
            `;
            const [filas] = await this.db.execute(query, [docenteId]);

            return filas.map(f => new Curso({
                id: f.id,
                nombre: f.nombre,
                nivel: f.nivel,
                letra: f.letra,
                anio: f.anio_lectivo,
                docenteId: f.id_profesor_jefe,
                totalEstudiantes: Number(f.total_estudiantes)
            }));
        }

        // Simulación en memoria basada en los datos del script BaseDatos.sql
        // Id 1: Diego Rubilar, Id 2: Mirko Massa (Profesor Jefe)
        const cursosMock = [
            { id: 101, nombre: "1° Medio A", nivel: "Enseñanza Media", letra: "A", anio_lectivo: 2026, id_profesor_jefe: 2, total_estudiantes: 32 },
            { id: 102, nombre: "2° Medio B", nivel: "Enseñanza Media", letra: "B", anio_lectivo: 2026, id_profesor_jefe: 2, total_estudiantes: 28 },
            { id: 103, nombre: "3° Medio A", nivel: "Enseñanza Media", letra: "A", anio_lectivo: 2026, id_profesor_jefe: 1, total_estudiantes: 30 }
        ];

        const cursosEncontrados = cursosMock.filter(c => c.id_profesor_jefe === docenteId);

        return cursosEncontrados.map(f => new Curso({
            id: f.id,
            nombre: f.nombre,
            nivel: f.nivel,
            letra: f.letra,
            anio: f.anio_lectivo,
            docenteId: f.id_profesor_jefe,
            totalEstudiantes: f.total_estudiantes
        }));
    }
}

module.exports = CursoRepository;