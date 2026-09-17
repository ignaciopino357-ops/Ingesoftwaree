-- Script de creación de base de datos: Sistema de Alerta Temprana de Deserción Escolar
-- Cada integrante del equipo debe correr este script en su propio MySQL local.

CREATE DATABASE IF NOT EXISTS alerta_desercion_escolar;
USE alerta_desercion_escolar;

CREATE TABLE Usuario (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol             ENUM('DOCENTE','PROFESOR_JEFE','CONVIVENCIA_ESCOLAR','UTP','DIRECTIVO') NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE Curso (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nombre            VARCHAR(100) NOT NULL,
    nivel             VARCHAR(50) NOT NULL,
    letra             CHAR(1),
    anio_lectivo      INT NOT NULL,
    id_profesor_jefe  INT,
    FOREIGN KEY (id_profesor_jefe) REFERENCES Usuario(id)
);

CREATE TABLE Estudiante (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    rut                 VARCHAR(12) NOT NULL UNIQUE,
    nombres             VARCHAR(100) NOT NULL,
    apellidos           VARCHAR(100) NOT NULL,
    id_curso            INT NOT NULL,
    nivel_riesgo_actual ENUM('BAJO','MEDIO','ALTO') DEFAULT 'BAJO',
    FOREIGN KEY (id_curso) REFERENCES Curso(id)
);

CREATE TABLE RegistroAcademico (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante  INT NOT NULL,
    fecha          DATE NOT NULL,
    asistencia     DECIMAL(5,2),
    nota           DECIMAL(3,1),
    FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id)
);

CREATE TABLE CasoIntervencion (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante   INT NOT NULL,
    motivo          ENUM('ACADEMICO','ASISTENCIA','CONDUCTUAL','SOCIOEMOCIONAL') NOT NULL,
    estado          ENUM('PENDIENTE','EN_PROCESO','RESUELTA') DEFAULT 'PENDIENTE',
    observaciones   TEXT,
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id)
);

CREATE TABLE Mensaje (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario_emisor INT NOT NULL,
    asunto            VARCHAR(150),
    contenido         TEXT,
    fecha             DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario_emisor) REFERENCES Usuario(id)
);

CREATE TABLE Reporte (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    periodo           VARCHAR(50),
    filtros           VARCHAR(255),
    formato           VARCHAR(20),
    fecha_generacion  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Datos de prueba (4 usuarios, contraseña "123456" para todos)
INSERT INTO Usuario (nombre_completo, email, password_hash, rol) VALUES
('Diego Rubilar', 'diego.docente@liceo.cl', '$2a$08$DTaPSyzh0psan5NVVUXIieoFHjbWKwErNo/BNLhax3efuADVLYX6a', 'DOCENTE'),
('Mirko Massa', 'mirko.jefe@liceo.cl', '$2a$08$DTaPSyzh0psan5NVVUXIieoFHjbWKwErNo/BNLhax3efuADVLYX6a', 'PROFESOR_JEFE'),
('Constanza Rodriguez', 'coni.convivencia@liceo.cl', '$2a$08$DTaPSyzh0psan5NVVUXIieoFHjbWKwErNo/BNLhax3efuADVLYX6a', 'CONVIVENCIA_ESCOLAR'),
('Ignacio Pino', 'ignacio.utp@liceo.cl', '$2a$08$DTaPSyzh0psan5NVVUXIieoFHjbWKwErNo/BNLhax3efuADVLYX6a', 'UTP');
