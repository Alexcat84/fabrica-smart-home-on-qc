# Cola de verificacion

Todo dato que este repositorio no conoce con certeza vive aqui hasta que alguien lo confirma contra la
fuente primaria. Es una cola de trabajo, no un apendice. La regla que la crea es ADR-001 en
`docs/DECISIONES.md`: no se inventan numeros de parte, precios ni afirmaciones de certificacion.

## Como se usa

1. Un campo `null` con `verificado: false` en `catalogo/` **debe** tener su fila aqui.
2. Cuando se verifica un dato: se actualiza el YAML, se pone `verificado: true`, se rellena
   `fuente_url` y se **borra** la fila de esta tabla, anotandola en el registro del final.
3. La verificacion de certificacion se hace sobre la marca impresa en la unidad fisica en recepcion,
   no sobre una pagina web. Los fabricantes envian variantes distintas del mismo nombre de modelo
   segun el mercado de destino.

## Leyenda de urgencia

| Urgencia | Significado | Plazo |
|---|---|---|
| **ALTA** | Bloquea una cotizacion, una compra o una inspeccion. No se puede vender sin esto. | Antes del primer proyecto pagado |
| **MEDIA** | Bloquea el diseno detallado o el margen real, pero no la propuesta inicial. | Antes de abrir cuentas de distribucion |
| **BAJA** | Mejora la precision del catalogo. No bloquea nada. | Continuo |

---

## URGENCIA ALTA

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | Bloquea |
|---|---|---|---|---|
| A-01 | **Certificacion cULus / cETL / CSA por SKU de todo dispositivo con `instalable_en_caja: true`.** Son 22 entradas del catalogo. Ninguna se puede especificar en un archivo de cliente mientras `certificacion` sea `null`: `validar.py` lo rechaza. | `catalogo/dispositivos.yaml`, campo `certificacion` | Marca impresa en la unidad fisica en recepcion; ficha tecnica del SKU norteamericano | Toda compra e instalacion |
| A-02 | **Ruta de control local de Lutron Caseta sin cuenta de fabricante.** Que modelo de puente expone interfaz local documentada. Si ninguno cumple, cae ADR-003 y hay que sustituir la solucion de referencia para cajas sin neutro, que es el caso mas frecuente del parque antiguo. | `catalogo/dispositivos.yaml`, `lutron-caseta-dimmer-sin-neutro` | Documentacion tecnica de Lutron; prueba en banco con la propiedad desconectada de internet | Toda instalacion en vivienda sin neutro |
| A-03 | **Modulo de montaje en dosel certificado para Canada.** La entrada `modulo-canopy-certificado` existe sin fabricante. Es el unico camino para "sin neutro y sin espacio en caja". El plan de negocio marca esta opcion como pendiente de identificar. | `catalogo/dispositivos.yaml`, `modulo-canopy-certificado` | Distribucion electrica (Nedco, Westburne, Guillevin); catalogos de fabricante | Cotizacion de reformas en vivienda antigua |
| A-04 | **Requisitos de apertura de cuenta de cada distribuidor**: numero de empresa, prueba de seguro, licencia exigida. `requiere_licencia` esta en `null` en nueve proveedores. | `catalogo/proveedores.yaml` | Contacto comercial directo con cada distribuidor | Precio de distribuidor, y con el todo el margen bruto |
| A-05 | **Precio de distribuidor real de todo el catalogo.** Los valores de proyecto de `paquetes/` son indicativos y hay que reconstruirlos desde precio real en cuanto haya cuentas. | `catalogo/dispositivos.yaml`, `precio_distribuidor_cad`; `paquetes/*.yaml` | Listas de precio de distribuidor tras abrir cuenta | Toda cotizacion |
| A-06 | **Estado vigente del linaje de cadena de suministro de camaras.** Antes de publicar cualquier afirmacion sobre una marca concreta ante el segmento vinculado al gobierno federal. | `catalogo/excluidos.yaml`, `camara-linaje-restringido` | Publicaciones gubernamentales vigentes | Propuestas al segmento principal de la Region de la Capital Nacional |
| A-07 | **Limite de duracion de sirena del reglamento municipal de ruido** en Ottawa, Gatineau, Montreal y todo municipio servido. Determina el temporizador de corte, que es obligatorio. | Plantillas de automatizacion de sirena (Fase 2) | Reglamentos municipales | Toda instalacion con sirena |

---

## URGENCIA MEDIA

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | Bloquea |
|---|---|---|---|---|
| M-01 | **Numero de certificacion ISED** de todo dispositivo con radio, incluidos los de bateria, que quedan fuera del regimen de certificacion electrica pero no del de radio. | `catalogo/dispositivos.yaml`, campo `ised` | Etiqueta del dispositivo; base de datos de ISED | Diseno detallado |
| M-02 | **Soporte real de RTSP y ONVIF de Reolink, modelo por modelo y version de firmware por version.** Varia dentro de la misma linea. | `catalogo/dispositivos.yaml`, `reolink-poe-camara` | Prueba en banco del modelo concreto antes de comprometer un lote | Compra por lotes de camaras |
| M-03 | **Rango de temperatura de operacion por modelo de camara**, hasta al menos treinta grados bajo cero. Las camaras de cuerpo plastico ya estan excluidas, pero el rango hay que confirmarlo tambien en las aprobadas. | `catalogo/dispositivos.yaml`, todas las camaras | Ficha tecnica del modelo | Instalacion exterior |
| M-04 | **Generacion de procesador de los equipos reacondicionados disponibles**, que determina el soporte de OpenVINO y de decodificacion por hardware. | `catalogo/dispositivos.yaml`, familias de computo | Inventario real de los reacondicionadores calificados | Dimensionado del controlador |
| M-05 | **Calificar al menos dos reacondicionadores canadienses concretos.** Criterios: garantia, consistencia de generacion entre lotes, continuidad del mismo modelo y plazo de reposicion. | `catalogo/proveedores.yaml`, `reacondicionadores-ca` | Contacto comercial | Continuidad de plataforma del controlador |
| M-06 | **Licencia de la version concreta de InfluxDB que se despliegue.** Ha cambiado entre versiones mayores y determina la obligacion del apendice de licencias. | `catalogo/software.yaml`, `influxdb` | Repositorio upstream de la version fijada | Apendice de licencias del cliente |
| M-07 | **Condiciones vigentes de la opcion comercial del plano de control de la malla** para uso comercial. | `catalogo/software.yaml`, `plano-control-malla` | Terminos del servicio | Cotizacion de la opcion comercial |
| M-08 | **Discrepancia de recuento de VLAN en el nivel M.** El cap. 8.1 fija cinco; el cap. 8.2.1 describe Management y Guest como presentes de M en adelante, lo que darian seis. Adoptado provisionalmente: Guest presente, Management plegado en Controller. | `paquetes/M-standard.yaml`, `vlans.discrepancia_fuente` | Autor del plan de negocio | Plantilla de red del nivel M |
| M-12 | **Bitrate del sub-stream por modelo de camara.** El minimo de subida publicado para el paquete M (10 Mbps) solo se sostiene si el sub-stream de cada camara ronda 0,5 Mbps. A 1 Mbps, dos visores concurrentes agotan el enlace y no queda margen para el hogar. El sub-stream es parametro de diseno, no valor heredado de la camara. | `clientes/*/cliente.yaml`, `camaras[].bitrate_substream_mbps` | Medicion en banco por modelo | Promesa de visionado remoto simultaneo en el nivel M |
| M-09 | **Fabricante y modelo de rele de carril DIN certificado para Canada.** | `catalogo/dispositivos.yaml`, `rele-din-certificado` | Distribucion electrica | Diseno de tablero de automatizacion en niveles L y XL |
| M-10 | **Compatibilidad de sonda de piso radiante** con la ya instalada. Es la causa habitual de que el reemplazo falle en obra. | `catalogo/dispositivos.yaml`, `termostato-piso-radiante` | Ficha tecnica del termostato y de la sonda existente | Instalacion de piso radiante |
| M-11 | **Ruta local de ecobee**: que funciones vendidas cubre realmente Matter o la interfaz local de HomeKit sin la nube del fabricante. | `catalogo/dispositivos.yaml`, `ecobee-termostato` | Prueba en banco con la propiedad desconectada de internet | Propuestas de aire forzado en Ontario |

---

## URGENCIA BAJA

| # | Que hay que verificar | Donde vive el dato | Fuente a consultar | Bloquea |
|---|---|---|---|---|
| B-01 | **Numeros de modelo concretos** de las familias donde `modelo` es `null`. Solo son necesarios al fijar el SKU de compra. | `catalogo/dispositivos.yaml`, campo `modelo` | Catalogo del distribuidor | Nada; mejora la precision del catalogo |
| B-02 | **Precio de lista** (`precio_lista_cad`). Util para calcular el descuento del distribuidor, no para cotizar. | `catalogo/dispositivos.yaml` | Retail publico | Nada |
| B-03 | **`contacto_url` de los dieciseis proveedores.** | `catalogo/proveedores.yaml` | Web de cada proveedor | Nada |
| B-04 | **Versiones a fijar de los veintisiete componentes de software.** Se fijan al estandarizar el banco de la empresa, no antes. | `catalogo/software.yaml`, `version_fijada` | Banco de pruebas de la empresa | Primer despliegue reproducible |
| B-05 | **Distribucion Linux concreta** para la opcion de anfitrion minimo con contenedores. | `catalogo/software.yaml`, `linux-minimo-con-contenedores` | Decision interna al estandarizar el banco | Nada |
| B-06 | **Cobertura provincial real de Memory Express**, antes de prometer plazos de entrega. | `catalogo/proveedores.yaml`, `memory-express` | Web del proveedor | Nada |

---

## Registro de verificaciones completadas

| Fecha | Dato | Resultado | Quien | Fuente |
|---|---|---|---|---|
| _(vacio)_ | | | | |
