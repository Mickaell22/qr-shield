# Índice de Documentos del Proyecto NovaTools — QR Shield

Resumen de los 8 documentos académicos de `Doc/` (Sprint 0, período 2026-2027 Ciclo I).
Proyecto: *Implementación de una solución multiplataforma para la identificación de
códigos QR y detección temprana de amenazas asociadas a ataques de quishing.*
Autor: Morán Vera Mickaell Adrián — Equipo: NovaTools — Tutora/PO: Ing. Angela Yanza Montalván.

---

## 1- Registro de Proyecto.md

Conversión del libro Excel original (hojas Portada, Anteproyecto, Anexo1).

- **Portada:** datos institucionales (Universidad de Guayaquil, FCMF, Carrera de Software, semestre 2026-2027 CI, modalidad Virtual), equipo **NovaTools**, líder **Morán Vera Mickaell Adrián**, fecha `2026-06-07`, tema completo del proyecto.
- **Anteproyecto:** problemática del quishing en Ecuador (67% de usuarios de billeteras digitales entre 18-35 años, alerta del Mintel jul-2025, crecimiento x5 ago-nov 2025), objetivo general + 4 específicos, justificación e importancia, recursos (humanos, hardware, software/servicios, bibliográficos), involucrados (beneficiarios directos e indirectos e institucionales).
- **Anexo1:** matriz de involucrados con **9 actores** clasificados por **Poder / Interés** (tutora y autor en Poder Alto / Interés Alto; estudiantes FCMF en Poder Bajo / Interés Alto).

---

## 2- Anteproyecto Moran Vera Mickaell.md

Propuesta formal de **Trabajo de Integración Curricular** (formato institucional UG).

- Línea de investigación: *Tecnologías, procesos y desarrollo industrial* / Sublínea: *Sistemas de información, seguridad, arquitectura de redes y software*. Tipo: **Proyecto Informático → Desarrollo de sistemas → Desarrollo Software UG**.
- Planteamiento del problema, objetivos (general + 4 específicos), **alcance** (incluye / no incluye), justificación **técnica y académica**.
- Metodología: investigación (cuantitativa/cualitativa) + **SCRUM adaptado a proyecto individual** (Daily Standups reemplazados por la bitácora de commits Conventional Commits).
- **Presupuesto $66 USD** (Railway $60 + dominio $6) y **cronograma de 6 actividades** abr-jul 2026.
- Incluye el formulario oficial de tipos de titulación (marcado *Desarrollo Software UG*), requisitos mínimos por tipo, datos de contacto y firma del estudiante.

---

## 3- Presentacion Proyecto.md

Versión resumida / orientada a diapositivas del anteproyecto. Tutor citado: **Ph.D. Jenny Ortiz Zambrano**.

- Tabla de contenido de 12 secciones: introducción, generalidades, tema/tipo, problemática, objetivos, alcance, justificación, metodología, recursos, presupuesto, cronograma, anexos.
- Resume el mismo contenido del anteproyecto en formato condensado (bullets y tablas).
- **Anexos:** originalidad del tema (búsqueda en biblioteca CISC y listado EP 2025-2026 C2), entorno de validación (FCMF-UG), y enlace a diapositivas en Canva.

---

## 4- Acta de Constitucion Moran Vera Mickaell.md

Acta de constitución (project charter) del proyecto.

- **Información del proyecto:** empresa ejecutora NovaTools-UG, fechas 01/04/2026 – 31/07/2026 (Sprint 0), patrocinador Ing. Angela Yanza Montalván, gerente Morán Vera Mickaell Adrián.
- Justificación, **objetivos con criterios SMART** (objetivo general: detectar/clasificar ≥ **85%** de URLs maliciosas usando el dataset histórico de PhishTank como benchmark; cobertura de pruebas unitarias ≥ 70%).
- Alcance dentro/fuera, **7 entregables principales**, requerimientos de alto nivel (**RNF / RF / RP**), supuestos, exclusiones, **5 riesgos** con mitigación, cronograma de hitos, presupuesto $66, registro de interesados, niveles de autoridad del gerente, equipo asignado y aprobaciones.

---

## 5- Matriz de requerimientos Moran Vera Mickaell.md

Matriz de **14 requerimientos** (RF-001 a RF-008, RNF-009 a RNF-014), cada uno con responsable, definición, complejidad, prioridad, urgencia (fecha límite), riesgo, criterio de aceptación, estatus (*En Análisis*) y fuente.

- **RF-001/002/003:** contrato del motor (URL → veredicto + score), esquema **multicapa L1-L5 en cascada con corto-circuito**, y heurísticas propias de L1 (acortadores, IP literal, longitud anómala, TLD sospechoso, punycode, desviación léxica).
- **RF-004/005/006:** extensión Chromium (detección de QR en página), app Flutter (cámara + galería, mín. Android 10/API 29), alerta semáforo antes de redirigir.
- **RF-007/008:** configuración de parámetros y telemetría anónima + panel de métricas.
- **RNF-009 a 014:** tiempo de respuesta **P95 ≤ 3s**, cumplimiento de la **LOPDP** (sin PII), compatibilidad Chromium MV3 y Android 10+, despliegue **HTTPS sobre Railway** con degradación controlada, y repositorio Git versionado.

---

## 6- EDT_NovaTools.md

**Estructura de Desglose del Trabajo (EDT/WBS)** del proyecto.

- `1.0` Sistema de detección de QR maliciosos para estudiantes de la FCMF-UG.
- `1.1` Documentación académica → `1.1.1` documento de titulación (Caps. 1, 2 y 3), `1.1.2` artefactos SCRUM.
- `1.2` Motor de detección → `1.2.1` backend HTTPS sobre Railway, `1.2.2` motor **multicapa L1-L5** (heurísticas + URLhaus + Google Safe Browsing + VirusTotal en cascada).
- `1.3` Frontends → `1.3.1` extensión Chromium (UI/UX + lógica de detección), `1.3.2` app móvil Flutter (UI/UX + escaneo cámara/galería).

---

## 7- Cronograma de Actividades - Moran Vera Mickaell.md

**Cronograma tipo Gantt** del Sprint 0 (período 01/04/2026 – 31/07/2026), con 6 actividades:

1. Aprobación del tema y planificación del Sprint 0 (01–07/04, 7 días).
2. Cap. 1: planteamiento, objetivos, justificación y alcance (08–28/04, 21 días).
3. Cap. 2: marco teórico (quishing, detección de QR, APIs, legal) (29/04–26/05, 28 días).
4. Cap. 3: metodología, SCRUM, población/muestra, factibilidad y arquitectura (27/05–23/06, 28 días).
5. Diseño y maquetación del front (extensión + app Flutter) (24/06–14/07, 21 días).
6. Revisión integral, correcciones y entrega final (15–31/07, 17 días).

---

## 8- Fases - Moran Vera Mickaell.md

Desarrollo del proyecto bajo la **Metodología de Marco Lógico** (7 fases).

- **Fase 1 — Análisis del Problema Central:** análisis causal con **10 causas/consecuencias** + diagrama de Ishikawa.
- **Fase 2 — Análisis de Involucrados:** matrices Poder-Interés, Influencia-Impacto y Poder-Influencia, y mapa de actores (9 involucrados).
- **Fase 3 — Análisis de Problemas:** árbol de problemas.
- **Fase 4 — Análisis de Objetivos:** árbol de objetivos.
- **Fase 5 — Análisis de Alternativas:** árbol de alternativas.
- **Fase 6 — Diseño Estratégico:** Estructura Analítica del Proyecto (EAP).
- **Fase 7 — Matriz de Marco Lógico (MML).**

---

*Índice de documentos del proyecto QR Shield — NovaTools.*
</content>
</invoke>
