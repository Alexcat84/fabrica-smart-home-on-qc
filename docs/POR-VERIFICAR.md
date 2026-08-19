# Cola de verificacion — tecnica y comercial

Todo dato que este repositorio no conoce con certeza vive aqui hasta que alguien lo confirma contra la
fuente primaria. Es una cola de trabajo, no un apendice. La regla que la crea es ADR-001 en
`docs/DECISIONES.md`: no se inventan numeros de parte, precios ni afirmaciones de certificacion.

> Las consultas a **organismos reguladores, aseguradoras y aduanas** viven aparte, en
> [POR-VERIFICAR-REGULATORIO.md](POR-VERIFICAR-REGULATORIO.md). Se separaron porque tienen otro
> ritmo, otro interlocutor y otra forma de cierre: piden respuesta escrita, no medicion.

## Como se usa

1. Un campo `null` con `verificado: false` en `datos-maestros/` **debe** tener su fila aqui.
2. Cuando se verifica un dato: se actualiza el YAML, se pone `verificado: true`, se rellena
   `fuente_url` y se **borra** la fila de esta tabla, anotandola en el registro del final.
3. La verificacion de certificacion se hace sobre la marca impresa en la unidad fisica en recepcion,
   no sobre una pagina web. Los fabricantes envian variantes distintas del mismo nombre de modelo
   segun el mercado de destino.

## Como esta ordenada

**Por lo que desbloquea, no por lo que cuesta.** La columna *Desbloquea* es la razon del orden: las
cuentas de distribucion van primero porque son el canal por el que se responden casi todas las demas
filas de urgencia ALTA. Una conversacion con el distribuidor resuelve precio, disponibilidad,
certificacion por SKU y buena parte del linaje de cadena de suministro. Empezar por A-01 sin cuenta
abierta significa perseguir veintidos fichas tecnicas una por una, y volver a empezar cuando el SKU
cambie.

Los identificadores **no se renumeran al reordenar**: el orden cambia, la referencia no, porque hay
codigo y documentos que apuntan a estas filas por su id.

## Acciones preparadas el 2026-08-19

Tres acciones **fuera del repositorio**, con el texto redactado y listo para enviar. Ninguna esta
enviada: enviarla es una accion humana, y la fecha de envio la rellena quien la envie.

| Fecha de preparacion | Accion | Fila | Borrador | Fecha de envio | Respuesta |
|---|---|---|---|---|---|
| 2026-08-19 | Consulta escrita al Bureau de la securite privee | **R-01** | [consultas/R-01-bureau-securite-privee.md](consultas/R-01-bureau-securite-privee.md) | _(pendiente)_ | _(pendiente)_ |
| 2026-08-19 | Solicitudes de cuenta corporativa a ADI Canada, Aartech y un distribuidor electrico quebequense, pidiendo ficha tecnica con marcado de certificacion de los 22 dispositivos de caja | **A-04**, **A-05**, y de rebote **A-01**, **A-06**, **A-08** | [consultas/A-04-A-05-cuentas-de-distribucion.md](consultas/A-04-A-05-cuentas-de-distribucion.md) | _(pendiente)_ | _(pendiente)_ |
| 2026-08-19 | Cotizacion del hardware del banco, incluidos coordinador Zigbee por Ethernet, dos camaras PoE de modelos distintos y switch PoE+ gestionado | **BANCO**, y de rebote **A-02**, **A-08**, **M-02**, **M-04**, **M-11**, **M-13**, **B-04** | [consultas/BANCO-cotizacion-hardware.md](consultas/BANCO-cotizacion-hardware.md) | _(pendiente)_ | _(pendiente)_ |

El orden importa: **R-01 no depende de las otras dos y bloquea mas que ninguna.** Las cuentas de
distribucion dependen de R-16 (prueba de seguro) solo en parte; se pueden enviar antes para saber
que documentacion piden. La cotizacion del banco no depende de nada y es el camino critico del
trabajo tecnico, porque los ocho roles de ansible no se escriben sin banco.

## Leyenda de urgencia

| Urgencia | Significado | Plazo |
|---|---|---|
| **ALTA** | Bloquea una cotizacion, una compra o una inspeccion. No se puede vender sin esto. | Antes del primer proyecto pagado |
| **MEDIA** | Bloquea el diseno detallado o el margen real, pero no la propuesta inicial. | Antes de abrir cuentas de distribucion |
| **BAJA** | Mejora la precision del catalogo. No bloquea nada. | Continuo |

---

## URGENCIA ALTA

### Primero: abrir el canal

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | **Desbloquea** |
|---|---|---|---|---|
| **A-04** | **Requisitos de apertura de cuenta de cada distribuidor**: numero de empresa, prueba de seguro, licencia exigida. `requiere_licencia` esta en `null` en nueve proveedores. | `datos-maestros/proveedores.yaml` | Contacto comercial directo con cada distribuidor | **A-05, A-01, A-06 y parte de A-02.** Es la puerta: sin cuenta no hay lista de precios, no hay ficha tecnica por SKU y no hay interlocutor a quien preguntar por linaje |
| **A-05** | **Precio de distribuidor real de todo el catalogo.** Los valores de proyecto de `comercial/paquetes/` son indicativos y hay que reconstruirlos desde precio real en cuanto haya cuentas. | `datos-maestros/dispositivos/`, `precio_distribuidor_cad`; `comercial/comercial/paquetes/*.yaml` | Listas de precio de distribuidor, tras A-04 | **Toda cotizacion**, y con ella el margen bruto, que es lo que decide si el negocio es viable |

### Despues: lo que el canal responde

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | **Desbloquea** |
|---|---|---|---|---|
| **A-01** | **Certificacion cULus / cETL / CSA por SKU de todo dispositivo con `instalable_en_caja: true`.** Son 22 entradas del catalogo. Ninguna se puede especificar en un archivo de cliente mientras `certificacion` sea `null`: `validador/validar.py` lo rechaza. | `datos-maestros/dispositivos/`, campo `certificacion` | Marca impresa en la unidad fisica en recepcion; ficha tecnica del SKU norteamericano, via A-04 | **Toda compra e instalacion.** Es la fila que mas dispositivos libera de golpe |
| **A-08** | **Inovelli Blue Series 2-1: operacion sin neutro y certificacion cETL.** Confirmar (a) que opera sin conductor neutro, (b) la marca cETL sobre la unidad fisica, y (c) **a partir de que carga exige modulo de bypass**, y cual es el modulo certificado. | `datos-maestros/dispositivos/`, `inovelli-blue-2-1` | Fabricante y Aartech Canada; prueba en banco con la lampara LED real | **La rama 2 del arbol de ADR-008 sin puente propietario.** Si sale a favor, la excepcion de Lutron (A-02) deja de ser necesaria y el catalogo vuelve a un solo ecosistema de radio |
| **A-02** | **Lutron Caseta: ruta de control local sin cuenta, y modulo de dosel certificado.** Dos preguntas que comparten decision: (a) que modelo de puente expone interfaz local documentada sin cuenta de fabricante; (b) que modulo de montaje en dosel certificado para Canada cubre el caso "sin neutro y sin espacio". *(Absorbe la antigua A-03.)* | `datos-maestros/dispositivos/`, `lutron-caseta-dimmer-sin-neutro` y `modulo-canopy-certificado` | Documentacion de Lutron; prueba en banco con la propiedad desconectada de internet; distribucion electrica para el dosel | **Las ramas 2 y 3 del arbol de ADR-008.** Si (a) sale en contra, Caseta pasa al registro de exclusion; si (b) no se resuelve, el caso "sin neutro y sin espacio" no tiene solucion aprobada y hay que decirlo en el relevamiento en lugar de improvisar en obra |
| **A-06** | **Estado vigente del linaje de cadena de suministro de camaras**, antes de publicar cualquier afirmacion sobre una marca concreta ante el segmento vinculado al gobierno federal. | `datos-maestros/excluidos.yaml`, `camara-linaje-restringido` | Publicaciones gubernamentales vigentes; distribuidor, via A-04 | **Propuestas al segmento principal** de la Region de la Capital Nacional, que es el mercado de lanzamiento |

### En paralelo: no depende del canal

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | **Desbloquea** |
|---|---|---|---|---|
| **A-07** | **Limite de duracion de sirena del reglamento municipal de ruido** en Ottawa, Gatineau, Montreal y todo municipio servido. Determina el temporizador de corte, que es obligatorio. | `producto-cliente/stack/homeassistant/packages/seguridad.yaml.j2`; `minutos_corte` en el archivo de cliente | Reglamentos municipales. Ver tambien R-13 en la cola regulatoria | **Toda instalacion con sirena.** Un temporizador mal puesto es una infraccion, no un detalle |

---

## URGENCIA MEDIA

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | **Desbloquea** |
|---|---|---|---|---|
| M-01 | **Numero de certificacion ISED** de todo dispositivo con radio, incluidos los de bateria, que quedan fuera del regimen de certificacion electrica pero no del de radio. | `datos-maestros/dispositivos/`, campo `ised` | Etiqueta del dispositivo; base de datos de ISED | Diseno detallado y as-built completo |
| M-02 | **Soporte real de RTSP y ONVIF de Reolink, modelo por modelo y version de firmware por version.** Varia dentro de la misma linea. | `datos-maestros/dispositivos/`, `reolink-poe-camara` | Prueba en banco del modelo concreto | Compra por lotes de camaras |
| M-03 | **Rango de temperatura de operacion por modelo de camara**, hasta al menos treinta grados bajo cero. | `datos-maestros/dispositivos/`, todas las camaras | Ficha tecnica del modelo | Instalacion exterior, que es casi toda |
| M-04 | **Generacion de procesador de los equipos reacondicionados disponibles**, que determina el soporte de OpenVINO y de decodificacion por hardware. | `datos-maestros/dispositivos/`, familias de computo | Inventario real de los reacondicionadores calificados | Dimensionado del controlador; ver `docs/BANCO.md` |
| M-05 | **Calificar al menos dos reacondicionadores canadienses concretos.** Criterios: garantia, consistencia de generacion entre lotes, continuidad del mismo modelo y plazo de reposicion. | `datos-maestros/proveedores.yaml`, `reacondicionadores-ca` | Contacto comercial | Continuidad de plataforma del controlador |
| M-06 | **Licencia de la version concreta de InfluxDB que se despliegue.** Ha cambiado entre versiones mayores y determina la obligacion del apendice de licencias. | `datos-maestros/software-cliente.yaml`, `influxdb` | Repositorio upstream de la version fijada | Apendice de licencias del cliente |
| M-07 | **Condiciones vigentes de la opcion comercial del plano de control de la malla** para uso comercial. | `datos-maestros/software-cliente.yaml`, `plano-control-malla` | Terminos del servicio. Ver tambien R-21 | Cotizacion de la opcion comercial |
| M-09 | **Fabricante y modelo de rele de carril DIN certificado para Canada.** | `datos-maestros/dispositivos/`, `rele-din-certificado` | Distribucion electrica, via A-04 | Tablero de automatizacion en niveles L y XL |
| M-10 | **Compatibilidad de sonda de piso radiante** con la ya instalada. Es la causa habitual de que el reemplazo falle en obra. | `datos-maestros/dispositivos/`, `termostato-piso-radiante` | Ficha tecnica del termostato y de la sonda existente | Instalacion de piso radiante |
| M-11 | **Ruta local de ecobee**: que funciones vendidas cubre realmente Matter o la interfaz local de HomeKit sin la nube del fabricante. | `datos-maestros/dispositivos/`, `ecobee-termostato` | Prueba en banco con la propiedad desconectada de internet | Propuestas de aire forzado en Ontario |
| M-14 | **Numero de flujos publicados, y bitrate y resolucion del flujo MEDIO, por modelo y firmware de camara.** Decide si abrir una camara en remoto sirve un intermedio o el principal, y esa diferencia decide si el enlace del sitio aguanta. `calc_ancho_banda.py` **falla** si falta `streams_soportados`: no se supone. | `datos-maestros/dispositivos/camara.yaml`, `streams_soportados`, `stream_medio_bitrate_mbps`, `stream_medio_resolucion` | Medicion en banco con el enlace estrangulado. Ver `docs/BANCO.md` | Los minimos de subida publicados de los cuatro paquetes. **Hoy son PROVISIONALES**: salen de un perfil de camara calculado, no de camaras medidas. Se publican para poder cotizar, no como promesa, y asi se presentan en el informe de relevamiento. El numero que decide un diseno concreto es siempre `red.subida_medida_mbps` de ese cliente, con su fecha y su metodo |
| M-13 | **Bitrate y resolucion del sub-stream, por modelo y firmware de camara.** Los campos existen y estan en `null`. Mientras lo esten, cada archivo de cliente tiene que declararlos o `validador/validar.py` lo rechaza. | `datos-maestros/dispositivos/`, `substream_bitrate_mbps` y `substream_resolucion` | Medicion en banco. Ver `docs/BANCO.md` | Que el archivo de cliente no tenga que medirlo sitio por sitio. *(Sucede a M-12, cerrada al implementar los dos escenarios.)* |

---

## URGENCIA BAJA

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | **Desbloquea** |
|---|---|---|---|---|
| B-01 | **Numeros de modelo concretos** de las familias donde `modelo` es `null`. | `datos-maestros/dispositivos/`, campo `modelo` | Catalogo del distribuidor | Nada; mejora la precision del catalogo |
| B-02 | **Precio de lista** (`precio_lista_cad`). Util para calcular el descuento del distribuidor, no para cotizar. | `datos-maestros/dispositivos/` | Retail publico | Nada |
| B-03 | **`contacto_url` de los dieciseis proveedores.** | `datos-maestros/proveedores.yaml` | Web de cada proveedor | Nada |
| B-04 | **Versiones a fijar de los veintisiete componentes de software.** | `datos-maestros/software-cliente.yaml`, `version_fijada` | Banco de la empresa. Procedimiento en `docs/BANCO.md` | Primer despliegue reproducible de verdad |
| B-05 | **Distribucion Linux concreta** para la opcion de anfitrion minimo con contenedores. | `datos-maestros/software-cliente.yaml`, `linux-minimo-con-contenedores` | Decision interna al estandarizar el banco | Nada |
| B-06 | **Cobertura provincial real de Memory Express**, antes de prometer plazos de entrega. | `datos-maestros/proveedores.yaml`, `memory-express` | Web del proveedor | Nada |

---

## Registro de verificaciones completadas

| Fecha | Dato | Resultado | Quien | Fuente |
|---|---|---|---|---|
| 2026-08-19 | **M-08**, discrepancia de recuento de VLAN en el nivel M | **Resuelta por ADR-009.** Management es VLAN separada de L en adelante; en S y M se pliega en Controller sin que las reglas de cortafuegos dejen de aplicarse. Recuento final 4 / 5 / 6 / 6, verificado por `herramientas-empresa/validador/test_vlans.py` sobre la plantilla renderizada | sesion 2 | Contradiccion interna entre los cap. 8.1 y 8.2.1 del plan, resuelta por criterio de diseno |
| 2026-08-19 | **M-12**, sub-stream como parametro de diseno | **Cerrada.** `substream_bitrate_mbps` y `substream_resolucion` anadidos al esquema de camara; `calc_ancho_banda.py` los lee del registro del dispositivo en lugar de una constante y evalua dos escenarios. Hallazgo asociado: **el minimo de 10 Mbps publicado para el paquete M cubre la vista general pero no que un visor abra una camara 4K en principal**, que pide 17,5 Mbps. La medicion por modelo pasa a M-13 | sesion 2 | Implementacion y prueba `test_el_minimo_publicado_del_paquete_m_no_sobrevive_al_escalamiento` |
| 2026-08-19 | **A-03**, modulo de dosel certificado | **Fusionada en A-02.** Las dos preguntas comparten decision: si Caseta no tiene ruta local sin cuenta, la rama 2 del arbol cae y el peso recae entero sobre el dosel de la rama 3 | sesion 2 | ADR-008 |
