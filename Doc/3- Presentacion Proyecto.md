# Implementación de una solución multiplataforma para la identificación de códigos QR y detección temprana de amenazas asociadas a ataques de quishing

**Universidad de Guayaquil — Facultad de Ciencias Matemáticas y Físicas**
**Carrera de Software**

| | |
|---|---|
| **Autores** | Morán Vera Mickaell Adrián |
| **Docente** | Ing. Angela Yanza Montalván |
| **Tutor** | Ph.D. Jenny Ortiz Zambrano |
| **Lugar** | Guayaquil, Ecuador |
| **Periodo Académico** | 2026 – 2027 CI |

---

## Tabla de Contenido

1. [Introducción](#01-introducción)
2. [Generalidades](#02-generalidades)
3. [Tema y Tipo de TT](#03-tema-y-tipo-de-tt)
4. [Problemática](#04-problemática)
5. [Objetivos](#05-objetivos)
6. [Alcance](#06-alcance)
7. [Justificación](#07-justificación)
8. [Metodología](#08-metodología)
9. [Recursos](#09-recursos)
10. [Presupuesto](#10-presupuesto)
11. [Cronograma](#11-cronograma)
12. [Anexos](#12-anexos)

---

## 01 Introducción

Los **códigos QR** son imágenes que codifican información y se leen con la cámara del celular.

Hoy son puerta de entrada a pagos, banca y accesos digitales en Ecuador.

El **Quishing** los suplanta o adultera para redirigir a **sitios fraudulentos** o instalar **malware**.

---

## 02 Generalidades

| Campo | Detalle |
|---|---|
| **Autor** | Morán Vera Mickaell Adrián |
| **Equipo** | NovaTools |
| **Docente** | Ing. Angela Yanza Montalván |
| **Línea de investigación** | Tecnologías, procesos y desarrollo industrial |
| **Sublínea** | Sistemas de información, seguridad, arquitectura de redes y software |

---

## 03 Tema y Tipo de TT

### Tema

Implementación de **una solución multiplataforma** para la identificación de **códigos QR** y **detección temprana** de amenazas asociadas a **ataques de quishing**.

### Tipo de Proyecto

**Proyecto Informático** → **Desarrollo de sistemas** → **Desarrollo Software UG**

---

## 04 Problemática

- **67%** de usuarios de billeteras digitales en Ecuador tienen entre **18 y 35 años**.
- **Estudiantes de la FCMF** expuestos a QR en wifi, cafetería, trámites, carteleras y banca dentro del **campus**.
- No existen herramientas locales que permitan verificar un QR antes de escanearlo.
- Los ataques de **quishing** se multiplicaron por 5 entre agosto y noviembre de 2025.

---

## 05 Objetivos

### Objetivo General

Desarrollar una **solución multiplataforma** para la identificación de **códigos QR** y la **detección temprana** de amenazas asociadas a ataques de **quishing**, dirigida a los **estudiantes de la Facultad de Ciencias Matemáticas y Físicas de la Universidad de Guayaquil**.

### Objetivos Específicos

- **Analizar** técnicas actuales de detección de QR maliciosos y vectores de ataque de quishing.
- **Diseñar** la arquitectura del sistema y el motor de detección de URL maliciosas.
- **Implementar** la extensión Chromium, la app Android y el motor de detección compartido.
- **Validar** técnicamente el sistema en escenarios de uso de los **estudiantes de la FCMF** con métricas de **precisión, exhaustividad y tiempo de respuesta**.

---

## 06 Alcance

### Qué Incluye

- Extensión para navegadores **Chromium** (Chrome, Edge, Brave)
- App móvil multiplataforma en **Flutter** (mínimo Android 10 / API 29) con escaneo de cámara y galería
- Motor de detección **multicapa (L1-L5) en cascada** con APIs de inteligencia de amenazas y heurísticas propias
- Alertas en **tiempo real** (semáforo verde/amarillo/rojo)

### Qué NO Incluye

- iOS y navegadores no Chromium
- Análisis más allá de la URL destino
- Publicación en Chrome Web Store o Google Play durante el período académico

---

## 07 Justificación

**Vacío en el mercado local:** No existen herramientas locales accesibles para verificar QR antes de escanearlos.

**Amenaza creciente y reconocida:** El quishing **creció x5 en 2025** y el Mintel ya lo declaró como riesgo nacional.

**Población con alta exposición:** Los **estudiantes de la FCMF** presentan **exposición diaria** a QR en el **campus**, en un entorno donde suplantar un código impreso es trivial.

**Aporte técnico verificable:** Se desarrolla **QR Shield**, una herramienta que analiza URLs extraídas de códigos QR mediante un **motor de detección multicapa** que combina heurísticas propias con fuentes de inteligencia de amenazas (**Google Safe Browsing, VirusTotal, URLhaus**) y emite una alerta antes de que el usuario acceda al sitio.

---

## 08 Metodología

### Metodología de investigación

**Cuasi-experimento** en laboratorio controlado. Pruebas con dataset de URLs etiquetadas (maliciosas y legítimas) para medir **precisión**, **exhaustividad** y **tiempo de respuesta** del motor de detección.

### Metodología de gestión del proyecto

**SCRUM** adaptado a proyecto individual. Sprints de 2 semanas, Product Owner = tutora, sin Daily Standups; la bitácora diaria de progreso se materializa mediante el historial de commits del repositorio (Conventional Commits).

### Metodología de desarrollo de software

**SCRUM** con prácticas ágiles. Product Backlog, Sprint Backlog, Sprint Review, Sprint Retrospective. Desarrollo iterativo e incremental del motor, la extensión y la app.

---

## 09 Recursos

### Humanos

- Autor del proyecto (estudiante de noveno semestre, certificación CEH)
- Tutora académica asignada por la carrera

### Software y Servicios

- Visual Studio Code, Flutter (Dart), Git, GitHub
- Railway para despliegue del backend
- APIs y feeds: Google Safe Browsing, VirusTotal, URLhaus

### Hardware

- Laptop de desarrollo
- PC de escritorio para backend y pruebas
- Dos dispositivos Android (gama media-alta y gama baja)

---

## 10 Presupuesto

| Concepto | Detalle | Costo |
|---|---|---|
| Recursos humanos | Estudiante desarrollador + tutora académica | $0 |
| Equipos de cómputo | Laptop, PC escritorio, 2 dispositivos Android | $0 |
| Software de desarrollo | VS Code, Flutter, Git, GitHub | $0 |
| APIs de inteligencia de amenazas | Google Safe Browsing, VirusTotal, URLhaus (nivel gratuito) | $0 |
| Despliegue backend | Railway (12 meses) | $60 |
| Dominio web | novamicktools.com (anual) | $6 |
| Recursos bibliográficos | IEEE, ACM, Google Scholar (acceso institucional UG) | $0 |
| **TOTAL** | Autofinanciado por el autor | **$66 USD** |

---

## 11 Cronograma

**Periodo:** Abril – Julio 2026

| Actividad | Inicio | Fin |
|---|---|---|
| Aprobación del tema y planificación del Sprint 0 | 01/04/2026 | 07/04/2026 |
| Capítulo 1: Planteamiento, objetivos, justificación y alcance | 08/04/2026 | 28/04/2026 |
| Capítulo 2: Marco teórico | 29/04/2026 | 26/05/2026 |
| Capítulo 3: Metodología, factibilidad y arquitectura | 27/05/2026 | 23/06/2026 |
| Diseño y maquetación del front (extensión y app) | 24/06/2026 | 14/07/2026 |
| Revisión integral y entrega final | 15/07/2026 | 31/07/2026 |

---

## 12 Anexos

### Originalidad del tema

- **Biblioteca CISC:** Búsqueda en el histórico de tesis de la carrera — sin resultados para "detección de QR maliciosos".
- **Listado de proyectos aprobados EP 2025-2026 C2:** El tema no aparece entre los proyectos aprobados del piloto.

### Entorno de validación

- **Facultad de Ciencias Matemáticas y Físicas, Universidad de Guayaquil** — entorno donde se validará el sistema con la población objetivo.
- Ejemplo visual del ataque de quishing que el sistema prevendrá: sustitución de QR físico impreso en espacios públicos del campus.

### Recursos adicionales

- Diapositivas en Canva: https://canva.link/1pizcuvittt91ps

---

*Morán Vera Mickaell Adrián — 07 de Junio del 2026*
