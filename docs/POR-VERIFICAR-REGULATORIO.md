# Cola de verificacion — regulatoria

Consultas a organismos reguladores, aseguradoras y aduanas. Salen del **capitulo 14 del plan de
negocio**, que consolida todo lo marcado `(V)` en el documento.

Estan separadas de [POR-VERIFICAR.md](POR-VERIFICAR.md) porque tienen otro ritmo, otro interlocutor y
otra forma de cierre. Una fila tecnica se cierra midiendo. Una fila regulatoria se cierra con una
**respuesta escrita del organismo**, fechada y archivada. La diferencia importa el dia que alguien
pregunte por que se hizo algo: "lo probamos en el banco" y "nos lo confirmo el regulador por escrito
el 12 de marzo" no son la misma clase de respuesta.

**Este es un documento controlado.** No se borran filas: se cierran, con fecha y con la respuesta
archivada.

## Reglas

1. **Respuesta escrita siempre que sea posible.** Una llamada telefonica se anota, pero no cierra una
   fila: se pide confirmacion por correo y se archiva.
2. **Fecha de consulta obligatoria.** Las respuestas regulatorias caducan. Una confirmacion de hace
   tres anos hay que releerla antes de apoyarse en ella.
3. **Nada de interpretar por nuestra cuenta.** Si la respuesta es ambigua, la fila sigue abierta y se
   repregunta. Una interpretacion optimista de un requisito de licencia es exactamente el error que
   cierra un negocio.
4. **Donde se archiva:** carpeta de la empresa, fuera de este repositorio. Aqui solo va el estado.
   Las respuestas pueden contener datos personales y no tienen por que estar en control de versiones.

## Estados

| Estado | Significado |
|---|---|
| `abierta` | Nadie ha preguntado todavia |
| `preparada` | Texto redactado y listo para enviar, con fecha de preparacion. **Todavia no enviado**: enviarlo es una accion humana y la fecha de envio la rellena quien lo envie |
| `consultada` | Preguntado, sin respuesta aun |
| `respondida` | Respuesta recibida, pendiente de aplicar al repositorio o al contrato |
| `cerrada` | Respuesta recibida, archivada y aplicada |
| `bloqueada` | Depende de otra fila o de un tramite previo |

---

## BLOQUEANTE DE VENTA

| # | Pregunta | Organismo | Estado | Fecha de consulta | Respuesta escrita | Que bloquea |
|---|---|---|---|---|---|---|
| **R-01** | **Instalar camaras IP y sensores locales sin panel de intrusion y sin monitoreo, ¿exige licencia de agencia de seguridad privada?** Se pregunta ademas si la respuesta cambia **con panel de intrusion y sirena local, sin monitoreo**. Texto listo en [consultas/R-01-bureau-securite-privee.md](consultas/R-01-bureau-securite-privee.md) | Bureau de la securite privee | `preparada` 2026-08-19 | _(pendiente de envio)_ | ☐ No | **TODA VENTA EN QUEBEC.** Es la primera llamada del negocio. Si la respuesta es que si, no se puede firmar ni un solo contrato en Quebec hasta tener la licencia, y el calendario y el coste de obtenerla cambian el plan financiero entero. Si es que no, **hay que conservar esa respuesta por escrito**: es la defensa si alguien lo cuestiona despues. Nada de lo que hay en este repositorio compensa equivocarse aqui |

---

## LICENCIAS Y HABILITACION PROFESIONAL

| # | Pregunta | Organismo | Estado | Fecha de consulta | Respuesta escrita | Que bloquea |
|---|---|---|---|---|---|---|
| R-02 | Requisitos del permiso de agente: coste, verificacion de antecedentes y plazos | Bureau de la securite privee | `bloqueada` por R-01 | — | ☐ No | Contratacion y calendario de arranque en Quebec |
| R-03 | Frontera exacta entre trabajo de baja tension sin licencia y trabajo que exige ECL, con ejemplos concretos | Electrical Safety Authority | `abierta` | — | ☐ No | Toda instalacion en Ontario. Determina que puede hacer la empresa y que hay que subcontratar a electricista licenciado |
| R-04 | Requisitos de ECL y de Master Electrician: umbral de experiencia vigente y tasas | Electrical Safety Authority | `abierta` | — | ☐ No | Operar en Ontario con trabajo de tension de linea propio en lugar de subcontratado |
| R-05 | Ruta de evaluacion de equivalencia de oficio para experiencia extranjera hacia el oficio 309A | Skilled Trades Ontario | `abierta` | — | ☐ No | Plan de personal y coste de mano de obra |
| R-06 | Subcategorias de licencia RBQ aplicables a electricidad y a sistemas de seguridad, y monto vigente de la fianza | Regie du batiment du Quebec | `abierta` | — | ☐ No | Toda instalacion en Quebec. Va junto a R-01 |
| R-07 | Condiciones de membresia en la CMEQ, cuotas y requisitos profesionales | CMEQ | `bloqueada` por R-06 | — | ☐ No | Contratacion electrica en Quebec: la membresia es obligatoria |
| R-08 | ¿Este alcance de trabajo cae dentro de la Ley R-20 y exige certificados de competencia de la CCQ? | Commission de la construction du Quebec | `abierta` | — | ☐ No | Estructura de personal en Quebec y coste por hora instalada |

---

## VENTA Y CONTRATACION

| # | Pregunta | Organismo | Estado | Fecha de consulta | Respuesta escrita | Que bloquea |
|---|---|---|---|---|---|---|
| R-09 | ¿Hacen falta permiso de comerciante itinerante y deposito de garantia para contratos firmados en el domicilio del cliente? | Office de la protection du consommateur | `abierta` | — | ☐ No | **La forma de cerrar una venta en Quebec.** Si hace falta, cambia donde se firma el contrato, no solo el papeleo |
| R-10 | Requisitos de contenido del acuerdo directo y restricciones vigentes de venta a domicilio | Ontario Ministry of Public and Business Service Delivery | `abierta` | — | ☐ No | Plantilla de contrato en Ontario |
| R-12 | Obligaciones linguisticas segun numero de empleados, y regla del contrato de adhesion | Office quebecois de la langue francaise | `abierta` | — | ☐ No | Los documentos de cliente ya se generan en frances (`producto-cliente/documentos/*.fr.md.j2`). Esta fila confirma si eso basta y desde que plantilla de empleados hay obligaciones adicionales |

---

## PROTECCION DE DATOS

| # | Pregunta | Organismo | Estado | Fecha de consulta | Respuesta escrita | Que bloquea |
|---|---|---|---|---|---|---|
| R-11 | Obligaciones de la Ley 25 para una empresa de este tamano, requisitos del registro de incidentes y umbrales de notificacion | Commission d'acces a l'information du Quebec | `abierta` | — | ☐ No | El procedimiento de `herramientas-empresa/runbooks/responder-incidente-seguridad.md` y la seccion 9 de `docs/SEGURIDAD.md` estan escritos con umbrales sin confirmar. Tambien la politica de privacidad publicada |

---

## OPERACION E INSTALACION

| # | Pregunta | Organismo | Estado | Fecha de consulta | Respuesta escrita | Que bloquea |
|---|---|---|---|---|---|---|
| R-13 | Limites del reglamento municipal de ruido para sirenas audibles, y requisitos de registro de alarmas | Ottawa, Gatineau, Montreal | `abierta` | — | ☐ No | El temporizador de corte de sirena, que es obligatorio. **Es la misma pregunta que A-07** en la cola tecnica: se responde una vez y se aplica en los dos sitios |
| R-14 | Estructuras y tarifas residenciales vigentes | Ontario Energy Board, Hydro-Quebec | `abierta` | — | ☐ No | Las propuestas de desplazamiento de carga en Ontario. Sin tarifa real no hay argumento de ahorro, solo una promesa |
| R-15 | Creditos de prima de seguro por deteccion de fuga y por dispositivos de seguridad, y si existe un programa de instalador reconocido | Intact, Desjardins, Aviva, Belairdirect, Co-operators | `abierta` | — | ☐ No | El argumento de venta del sensor de fuga, que el plan identifica como el de mayor valor percibido del mercado canadiense. Si el credito no existe o exige instalador reconocido, el argumento cambia |
| R-16 | Primas de responsabilidad civil general y de errores y omisiones para esta actividad y alcance | Corredor de seguros comercial | `abierta` | — | ☐ No | **La apertura de cuentas de distribucion (A-04):** varias exigen prueba de seguro. Tambien el limite de 2.000.000 CAD que el plan da por supuesto |
| R-17 | Tratamiento arancelario y aduanero vigente para las categorias de dispositivo de la lista de materiales | Canada Border Services Agency, agente de aduanas | `abierta` | — | ☐ No | El coste real del hardware cuando algo no se puede comprar dentro de Canada. Es tambien el argumento cuantitativo de la regla de aprovisionamiento canadiense |

---

## Items 18 a 24 del capitulo 14

Los siete restantes del capitulo 14 son verificaciones **tecnicas y de proveedor**, no regulatorias.
Ya viven en [POR-VERIFICAR.md](POR-VERIFICAR.md) y no se duplican aqui:

| Cap. 14 | Pregunta | Donde vive |
|---|---|---|
| 18 | Estado de certificacion canadiense, por SKU, de cada dispositivo del catalogo | **A-01** |
| 19 | Soporte de RTSP y ONVIF por modelo de camara y version de firmware | **M-02** |
| 20 | Linaje de cadena de suministro y estado de restriccion de cada marca de camara | **A-06** |
| 21 | Terminos de licencia comercial del plano de control de acceso remoto | **M-07** |
| 22 | Precio de distribuidor y requisitos de cuenta, por proveedor | **A-04** y **A-05** |
| 23 | Aplicabilidad de la formacion de trabajo en altura y seguridad en construccion a este alcance | *Sin fila.* Ver abajo |
| 24 | Practica de traduccion de direcciones de nivel de operador y disponibilidad de direccion estatica, por proveedor de internet | *Sin fila propia:* se releva por cliente, campo `red.cgnat` |

El item 23 no tiene fila en ninguna de las dos colas. Es una obligacion de **seguridad laboral**, no
de producto: aplica a instalar camaras en fachada y tender cable en desvan, que es trabajo en altura
real. Deberia abrirse como **R-18** dirigida al Ontario Ministry of Labour y a ASP Construction en
cuanto haya personal contratado. Se deja anotado aqui en lugar de crearlo vacio, para no simular
cobertura que todavia no existe.

---

## Registro de respuestas archivadas

| Fecha | Fila | Organismo | Respuesta recibida | Donde esta archivada | Aplicada al repositorio |
|---|---|---|---|---|---|
| _(vacio)_ | | | | | |
