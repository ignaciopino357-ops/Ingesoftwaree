// src/domain/models/curso.js
// Entidad pura del dominio de negocio (Hexagonal)

class Curso {
    constructor({ id, nombre, nivel, letra, anio, docenteId, totalEstudiantes }) {
        this.id = id;
        this.nombre = nombre;
        this.nivel = nivel;
        this.letra = letra;
        this.anio = anio;
        this.docenteId = docenteId;
        this.totalEstudiantes = totalEstudiantes || 0;
    }

    esDelDocente(docenteId) {
        return this.docenteId === docenteId;
    }
}

module.exports = Curso;