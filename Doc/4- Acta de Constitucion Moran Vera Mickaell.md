1.  **Información del Proyecto**

| Empresa Ejecutora | NovaTools — Universidad de Guayaquil, FCMF, Carrera de Software |
|----|----|
| Nombre del Proyecto | Implementación de una solución multiplataforma para la identificación de códigos QR y detección temprana de amenazas asociadas a ataques de quishing |
| Fecha de Inicio | 01/04/2026 |
| Fecha de Finalización esperada | 31/07/2026 (Sprint 0) — Ciclo académico 2026-2027 Ciclo I |
| Cliente o Contratante | Unidad de Integración Curricular — Universidad de Guayaquil |
| Patrocinador del Proyecto | Ing. Angela Yanza Montalván — Docente FCMF, Universidad de Guayaquil |
| Gerente de Proyecto | Morán Vera Mickaell Adrián |
| Meta/Objetivo del Proyecto | Desarrollar una solución multiplataforma para la identificación de códigos QR y la detección temprana de amenazas asociadas a ataques de quishing, dirigida a los estudiantes de la Facultad de Ciencias Matemáticas y Físicas de la Universidad de Guayaquil. |
| Alcance del Proyecto | Motor de detección multicapa (L1-L5) en cascada con corto-circuito, que combina heurísticas propias con fuentes de inteligencia de amenazas (Google Safe Browsing, VirusTotal, URLhaus), dos frontends (extensión Chromium y app móvil en Flutter) y validación técnica con dataset etiquetado realizada en escenarios de uso de los estudiantes de la Facultad de Ciencias Matemáticas y Físicas de la Universidad de Guayaquil. Excluye iOS, navegadores no Chromium, sandboxing y mantenimiento post-entrega. |

2.  **Justificación del Proyecto**

| El quishing (phishing mediante códigos QR) representa una amenaza creciente a nivel global: de acuerdo con el Ministerio de Telecomunicaciones y Sociedad de la Información del Ecuador, los intentos de fraude digital han aumentado de forma sostenida en los últimos años, y entidades financieras como Banco Pichincha han emitido alertas específicas sobre el uso malicioso de QR para redirigir a usuarios hacia sitios falsos o instalar malware. A diferencia del phishing tradicional, la URL incrustada en un QR no es visible al usuario antes de escanear, lo que elimina la posibilidad de inspección visual previa. A pesar de la magnitud del problema, no existe en el mercado ecuatoriano una solución integrada —extensión de navegador más aplicación móvil— que analice códigos QR en tiempo real antes de que el usuario acceda al enlace. El presente proyecto aborda este vacío mediante el desarrollo de QR Shield, solución del equipo NovaTools conformada por dos frontends (extensión Chromium y app móvil) que comparten un motor de detección multicapa basado en heurísticas propias complementadas con fuentes externas de inteligencia de amenazas (Google Safe Browsing, VirusTotal, URLhaus), constituyendo así la contribución académica diferenciadora. La implementación y validación se centra en los estudiantes de la Facultad de Ciencias Matemáticas y Físicas de la Universidad de Guayaquil, como entorno de alta exposición diaria a códigos QR dentro del campus. |
|----|

3.  **Objetivos del Proyecto y Criterios de éxito medibles**

| **Objetivo** | **Criterio de Éxito SMART** |
|----|----|
| GENERAL: Desarrollar una solución multiplataforma para la identificación de códigos QR y la detección temprana de amenazas asociadas a ataques de quishing, mediante un motor de análisis multicapa basado en heurísticas propias y fuentes de reputación de URLs, dirigida a los estudiantes de la Facultad de Ciencias Matemáticas y Físicas de la Universidad de Guayaquil. | El sistema detecta y clasifica correctamente al menos el 85 % de URLs maliciosas de un conjunto de prueba estándar (dataset histórico de PhishTank usado como benchmark de validación), validado dentro del cierre del Sprint 0 (31/07/2026). |
| ESPECÍFICO 1: Analizar el panorama de amenazas de quishing documentado en Ecuador y los mecanismos de detección de URLs maliciosas disponibles mediante APIs públicas. | Entrega de informe de análisis con mínimo 5 fuentes académicas o institucionales, revisado y aprobado por la tutora en la semana 3 del Sprint 0. |
| ESPECÍFICO 2: Diseñar la arquitectura del motor de detección compartido y las interfaces de usuario de la extensión Chromium y la app Android. | Diagramas de arquitectura (UML, flujo de datos) y prototipos de interfaz aprobados por la tutora durante el Sprint 0 (junio 2026). |
| ESPECÍFICO 3: Implementar el motor de detección y los dos frontends (extensión + app) con integración a Google Safe Browsing, VirusTotal y URLhaus. | Código funcional con cobertura de pruebas unitarias \>= 70 %, desplegado en entorno de staging (Railway) antes del cierre del Sprint 0 (31/07/2026). |
| ESPECÍFICO 4: Validar técnicamente el funcionamiento del sistema mediante pruebas con un conjunto representativo de códigos QR maliciosos y legítimos en escenarios de uso de los estudiantes de la Facultad de Ciencias Matemáticas y Físicas de la Universidad de Guayaquil, evaluando métricas de precisión, exhaustividad (recall) y tiempo de respuesta. | Reporte de validación técnica con dataset etiquetado (maliciosos y legítimos) ejecutado sobre escenarios representativos de los estudiantes de la FCMF, documentando precisión, recall y tiempo de respuesta promedio del motor de detección, entregado antes del cierre del Sprint 0 (31/07/2026). |

4.  **Alcance del Proyecto**

### **<u>Descripción general del proyecto</u>**

El proyecto desarrollará un motor de detección de URLs maliciosas
provenientes de códigos QR, diseñado como motor multicapa (L1-L5) en
cascada con corto-circuito y expuesto como servicio compartido para dos
productos: (1) una extensión de navegador para Chromium que intercepta
la URL al escanear un QR desde el navegador y (2) una aplicación móvil
en Flutter que lee el QR con la cámara del dispositivo. Ambos frontends
consultarán el motor en tiempo real y mostrarán al usuario una alerta de
seguridad antes de redirigirlo. La validación se realizará en escenarios
de uso de los estudiantes de la Facultad de Ciencias Matemáticas y
Físicas de la Universidad de Guayaquil como población empírica
representativa del entorno del campus.

### **<u>Alcance</u>**

<table>
<colgroup>
<col style="width: 50%" />
<col style="width: 50%" />
</colgroup>
<thead>
<tr>
<th style="text-align: center;"><strong>Dentro del Alcance</strong></th>
<th style="text-align: center;"><strong>Fuera del Alcance</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td><ul>
<li><p>Motor de detección de URLs maliciosas desplegado como servicio
HTTPS, diseñado como motor multicapa (L1-L5) en cascada con
corto-circuito que combina heurísticas propias con Google Safe Browsing,
VirusTotal y URLhaus</p></li>
</ul>
<ul>
<li><p>Extensión para navegadores Chromium (Chrome, Edge, Brave,
Opera)</p></li>
<li><p>Aplicación móvil en Flutter (versión mínima Android 10.0, API 29)
con escaneo de QR físicos por cámara</p></li>
<li><p>Mecanismo de alerta al usuario en tiempo real indicando el nivel
de riesgo antes de interactuar con el contenido del QR</p></li>
<li><p>Validación técnica con dataset de URLs etiquetadas (maliciosas y
legítimas), midiendo precisión, exhaustividad y tiempo de
respuesta</p></li>
<li><p>Documentación técnica (manual técnico, manual de usuario) y
artefactos SCRUM adaptado (historias de usuario, product backlog, sprint
backlogs, burndown chart)</p></li>
</ul></td>
<td><ul>
<li><p>Desarrollo de versiones para iOS o navegadores no basados en
Chromium (Firefox, Safari)</p></li>
<li><p>Capacidad de reparación o neutralización de QR maliciosos; el
sistema solo detecta y alerta</p></li>
<li><p>Publicación de la extensión en la Chrome Web Store ni de la
aplicación en Google Play durante el período académico</p></li>
<li><p>Análisis profundo del contenido de sitios destino más allá de la
clasificación de la URL; el sistema no ejecuta sandboxing ni descarga
contenido para inspección</p></li>
<li><p>Integración con sistemas de pago o banca móvil de entidades
financieras</p></li>
<li><p>Mantenimiento del sistema posterior a la entrega del proyecto
académico Capacitación formal a usuarios finales</p></li>
</ul></td>
</tr>
</tbody>
</table>

5.  **Listado de Entregables Principales**

| **\#** | **Entregable** | **Descripción** |
|----|----|----|
| 1 | **Informe de análisis de amenazas** | Documentación del panorama de quishing en Ecuador y revisión de APIs de detección disponibles. |
| 2 | **Documento de arquitectura y diseño** | Diagramas UML, flujo de datos del motor compartido y prototipos de interfaz (extensión + app). |
| 3 | **Motor de detección (backend)** | Servicio REST desplegado en Railway que recibe una URL y retorna veredicto de seguridad. |
| 4 | **Extensión Chromium v1.0** | Extensión empaquetada (.crx) con funcionalidad de intercepción y alerta de QR maliciosos. |
| 5 | **Aplicación Android v1.0** | APK con lector de QR integrado, consulta al motor y pantalla de alerta. |
| 6 | **Reporte de validación técnica** | Resultados de pruebas con dataset etiquetado: métricas de precisión, recall y tiempo de respuesta del motor de detección. |
| 7 | **Documentación técnica final** | Manual de instalación, código fuente en GitHub y memoria del proyecto académico. |

6.  **Requerimientos Alto Nivel del Producto**

| **\#** | **Requerimiento** |
|----|----|
| **RNF-01** | El sistema debe responder a cada consulta de verificación de URL en menos de 3 segundos bajo condiciones normales de red. |
| **RNF-02** | La extensión debe ser compatible con Chrome \>= 110, Edge \>= 110 y Brave \>= 1.50. |
| **RNF-03** | La aplicación Android debe funcionar en dispositivos con Android \>= 10 (API 29) y cámara trasera disponible. |
| **RF-01** | El motor debe evaluar cada URL mediante su esquema multicapa, consultando al menos las fuentes locales (heurísticas y URLhaus) y, cuando corresponda, las APIs externas (Google Safe Browsing, VirusTotal) según el flujo en cascada. |
| **RF-02** | El sistema debe mostrar una alerta clara al usuario (rojo/amarillo/verde) antes de permitir la navegación al enlace del QR. |
| **RF-03** | La extensión debe interceptar el evento de escaneo de QR en el navegador sin requerir que el usuario copie la URL manualmente. |
| **RF-04** | La app debe poder leer QR desde la cámara en tiempo real sin necesidad de capturar y guardar la imagen. |

7.  **Requerimientos Alto Nivel del Proyecto**

| **\#** | **Requerimiento** |
|----|----|
| **RP-01** | El proyecto debe seguir la metodología SCRUM adaptada para desarrollo individual: sprints de 2 semanas, Product Owner = tutora académica, sin Daily Standups, con bitácora diaria materializada mediante el historial de commits del repositorio (Conventional Commits). |
| **RP-02** | El código fuente debe mantenerse en repositorio Git (GitHub) con commits por funcionalidad y documentación de cada sprint. |
| **RP-03** | El proyecto debe contar con auspicio formal (firma de acta) de la Ing. Angela Yanza Montalván dentro del Sprint 0. |
| **RP-04** | El presupuesto de APIs externas no debe superar los límites del tier gratuito de Google Safe Browsing y VirusTotal durante el período académico. |
| **RP-05** | Todos los documentos académicos deben seguir las normas de citación APA 7.ª edición y ser entregados en los plazos establecidos por el docente. |

8.  **Supuestos**

<table style="width:99%;">
<colgroup>
<col style="width: 98%" />
</colgroup>
<thead>
<tr>
<th><ol type="1">
<li><p>Las APIs y feeds de Google Safe Browsing, VirusTotal y URLhaus
mantendrán disponibilidad &gt;= 99 % y sus endpoints no cambiarán
durante el período de desarrollo (abril–julio 2026).</p></li>
<li><p>La Ing. Angela Yanza Montalván continuará como tutora académica
durante todo el semestre y brindará retroalimentación dentro de los 5
días hábiles siguientes a cada entrega de sprint.</p></li>
<li><p>El desarrollador dispondrá de acceso continuo a los equipos de
desarrollo (ASUS TUF Dash F15, PC de escritorio) y a los dos
dispositivos Android de prueba.</p></li>
<li><p>La infraestructura de Railway mantendrá los planes gratuitos
disponibles para el despliegue del backend durante el período
académico.</p></li>
<li><p>Los estudiantes de la FCMF seleccionados para la validación
participarán voluntariamente y contarán con un dispositivo Android
compatible.</p></li>
<li><p>Los requisitos funcionales del sistema no experimentarán cambios
mayores después de la aprobación del diseño de arquitectura durante el
Sprint 0.</p></li>
</ol></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

9.  **Exclusiones**

| 1\. Soporte para navegadores distintos de la familia Chromium (Firefox, Safari, Opera legacy). 2. Versión iOS de la aplicación móvil: el entorno de compilación (macOS + Xcode) no está disponible. 3. Panel de administración web para gestión centralizada de reportes: fuera del alcance académico. 4. Soporte multilingüe: la interfaz se desarrollará únicamente en español. 5. Mantenimiento correctivo o evolutivo posterior a la entrega académica final. 6. Integración directa con sistemas institucionales de la UG (SIUG, correo corporativo). 7. Monetización o publicación en tiendas oficiales (Chrome Web Store, Google Play) dentro del período académico |
|----|

10. **Riesgos iniciales de alto nivel**

| **Riesgo** | **Probabilidad** | **Impacto** | **Estrategia de Mitigación** |
|----|----|----|----|
| Cambio de política o límites de cuota en las APIs externas (Google Safe Browsing, VirusTotal) | **Media** | **Alto** | Monitorear los dashboards de cuota semanalmente; el feed local de URLhaus y las heurísticas propias operan sin límites de cuota y sirven como respaldo ante restricciones de las APIs externas. |
| Alcance subestimado para desarrollo individual en el tiempo académico disponible | **Alta** | **Alto** | Priorizar el MVP (motor + un frontend) en los primeros sprints; el segundo frontend como entregable diferido si hay riesgo de tiempo. |
| Falta de auspicio formal de la tutora antes del inicio de desarrollo | **Baja** | **Alto** | Gestionar la firma del acta de constitución con la tutora académica como prioridad dentro del Sprint 0, en cuanto se confirme la designación formal por parte de la carrera. |
| Baja participación de los estudiantes de la FCMF en la fase de validación | **Media** | **Medio** | Coordinar con la facultad con antelación; ofrecer sesiones cortas de 15 minutos por participante para facilitar la convocatoria. |
| Incompatibilidades entre versiones de la API de la extensión Chromium (Manifest V3) | **Media** | **Medio** | Desarrollar desde el inicio con Manifest V3; consultar documentación oficial antes de diseñar la arquitectura de la extensión. |

11. **Cronograma de Fechas Claves** **e Hitos**

| **Actividad / Hito** | **Fecha de Inicio** | **Fecha de Fin** | **Descripción** |
|----|----|----|----|
| **Aprobación del tema y planificación del Sprint 0** | 01/04/2026 | 07/04/2026 | Registro oficial del proyecto; firma del acta de constitución con la tutora. |
| **Sprint 0 – Capítulo 1: planteamiento del problema, objetivos, justificación, delimitación y alcance** | 08/04/2026 | 28/04/2026 | Producción del primer capítulo del documento de titulación. |
| **Sprint 0 – Capítulo 2: marco teórico sobre quishing, técnicas de detección de QR maliciosos, APIs de inteligencia de amenazas y fundamentación legal** | 29/04/2026 | 26/05/2026 | Marco referencial completo para sustentar el desarrollo. |
| **Sprint 0 – Capítulo 3: metodología de investigación, SCRUM adaptado, población y muestra, análisis de factibilidad y diseño de arquitectura del sistema** | 27/05/2026 | 23/06/2026 | Definición metodológica y arquitectura técnica del sistema. |
| **Sprint 0 – Diseño y maquetación del front de la extensión Chromium y la app Android** | 24/06/2026 | 14/07/2026 | Prototipos de interfaz de usuario para ambos productos. |
| **Revisión integral, correcciones con la tutora y entrega final del documento** | 15/07/2026 | 31/07/2026 | Cierre del Sprint 0; entrega académica formal del anteproyecto. |

12. **Presupuesto estimado**

<table>
<colgroup>
<col style="width: 50%" />
<col style="width: 25%" />
<col style="width: 25%" />
</colgroup>
<thead>
<tr>
<th style="text-align: center;"><strong>Rubro</strong></th>
<th style="text-align: center;"><strong>Tipo</strong></th>
<th style="text-align: center;"><strong>Costo Estimado
(USD)</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>1 estudiante desarrollador — autor del proyecto (Morán Vera Mickaell
Adrián)</td>
<td>Recurso Humano</td>
<td>$ 0 (proyecto académico)</td>
</tr>
<tr>
<td>1 tutora académica — Ing. Angela Yanza Montalván</td>
<td>Recurso Humano</td>
<td>$ 0 (asignación institucional)</td>
</tr>
<tr>
<td>Laptop ASUS TUF Dash F15 y PC de escritorio Intel Core i7</td>
<td>Hardware (existente)</td>
<td>$ 0 (equipos personales)</td>
</tr>
<tr>
<td>Dos dispositivos Android para pruebas</td>
<td>Hardware (existente)</td>
<td>$ 0 (equipos personales)</td>
</tr>
<tr>
<td>Railway (plan Hobby para despliegue del backend)</td>
<td>Infraestructura</td>
<td>$ 60 ($ 5 mensuales x 12 meses)</td>
</tr>
<tr>
<td>Dominio novamicktools.com</td>
<td>Infraestructura</td>
<td>$ 6 (pago anual)</td>
</tr>
<tr>
<td>Google Cloud Console + APIs y feeds externos (Google Safe Browsing,
VirusTotal, URLhaus)</td>
<td>APIs</td>
<td>$ 0 (niveles gratuitos)</td>
</tr>
<tr>
<td>Acceso a IEEE Xplore, ACM Digital Library, Google Scholar</td>
<td>Recursos Materiales</td>
<td>$ 0 (acceso institucional UG)</td>
</tr>
<tr>
<td>Internet domiciliario y energía eléctrica</td>
<td>Recursos Materiales</td>
<td>$ 0 (servicio personal)</td>
</tr>
<tr>
<td><strong>TOTAL ESTIMADO</strong></td>
<td></td>
<td><strong>~ $66 USD (autofinanciado por el autor)</strong></td>
</tr>
<tr>
<td colspan="3">Fuente de financiamiento: Recursos propios del
desarrollador</td>
</tr>
</tbody>
</table>

13. **Registro de Interesados previamente identificados**

| **Nombre / Entidad** | **Rol** | **Categoría** | **Interés principal** |
|----|----|----|----|
| **Ing. Angela Yanza Montalván** | Tutora académica / Product Owner | Directo | Aprobación y auspicio del proyecto; calidad académica. |
| **Morán Vera Mickaell Adrián** | Desarrollador / Gerente de Proyecto | Directo | Aprobación del proyecto; base para tesis; aprendizaje técnico. |
| **Estudiantes de la FCMF** | Usuarios de validación | Directo | Herramienta funcional que proteja la seguridad de los estudiantes al escanear QR en el campus. |
| **Universidad de Guayaquil — FCMF** | Institución académica | Institucional | Calidad del proyecto en el repositorio institucional. |
| **Ministerio de Telecomunicaciones (Ecuador)** | Referente institucional | Indirecto | Evidencia de amenazas de fraude digital en Ecuador. |
| **Banco Pichincha** | Referente del sector financiero | Indirecto | Alertas sobre QR maliciosos como sustento del problema. |
| **Google (Safe Browsing API)** | Proveedor de API | Indirecto | Uso responsable dentro del tier gratuito. |
| **VirusTotal / Alphabet** | Proveedor de API | Indirecto | Cumplimiento de términos de uso de la API gratuita. |
| **URLhaus / abuse.ch** | Proveedor de feed de amenazas | Indirecto | Uso de feed abierto de URLs maliciosas para detección en vivo. |

14. **Gerente de Proyecto**

| **Nombre** | **Email** | **Cargo** | **Departamento** |
|:--:|:--:|:--:|:--:|
| Morán Vera Mickaell Adrián | mickael.moranver@ug.edu.ec | Desarrollador Full Stack — Gerente de Proyecto | Carrera de Software, FCMF — Universidad de Guayaquil |

## 

15. **Niveles de autoridad del Gerente de Proyecto**

| **Área de autoridad** | **Descripción del nivel de autoridad** |
|----|:---|
| Asignación del equipo y recursos | ALTO: Al ser un proyecto de desarrollo individual, el Gerente de Proyecto tiene autoridad total sobre la planificación y asignación de tareas por sprint, dado que no existen otros miembros de equipo que requieran coordinación externa. |
| Gestión de presupuesto y límites de variación | ALTO: El presupuesto es autofinanciado por el autor. El Gerente administra directamente los recursos económicos del proyecto. Cualquier gasto no previsto debe ser evaluado y decidido por el propio Gerente antes de ejecutarse. |
| Límites de aprobaciones | MEDIO: El Gerente aprueba decisiones técnicas de arquitectura, stack tecnológico y diseño del sistema. La aprobación de entregables académicos formales (capítulos del documento de titulación, prototipos) corresponde a la tutora académica, Ing. Angela Yanza Montalván, en su rol de Product Owner. |
| Gestión de tiempo y límites de variaciones | ALTO: El Gerente define y ajusta el cronograma de sprints. Variaciones que afecten la fecha de entrega final del Sprint 0 (31/07/2026) deben ser comunicadas y acordadas con la tutora académica. |

16. **Equipo asignado preliminarmente**

| **Nombre** | **Cargo** | **Departamento** |
|:--:|:--:|:--:|
| **Morán Vera Mickaell Adrián** | **Scrum Master / Developer** | **Carrera de Software, FCMF — UG** |
| **Ing. Angela Yanza Montalván** | **Product Owner (tutora académica)** | **Carrera de Software, FCMF — UG** |

17. **Aprobaciones**

|                            |                             |
|:--------------------------:|:---------------------------:|
| Morán Vera Mickaell Adrián | Ing. Angela Yanza Montalván |
