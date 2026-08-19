# Esquema del registro de dispositivo

Este texto era la cabecera del antiguo `catalogo/dispositivos.yaml`. Se conserva aqui, entero,
porque describe reglas que siguen vigentes y que ahora aplican a los archivos de este
directorio. El esquema ejecutable esta en `datos-maestros/esquemas/dispositivo.schema.json`.

```
# Catalogo de dispositivos aprobados
#
# REGLA ADR-001: no se inventan numeros de parte, precios ni certificaciones. Todo campo que no se
# conozca con certeza va en `null`, con `verificado: false`, y tiene su fila en docs/POR-VERIFICAR.md.
# Las entradas estan a nivel de FAMILIA de producto. El SKU concreto se fija al abrir la cuenta de
# distribucion y se verifica contra la marca impresa en la unidad fisica, en recepcion.
#
# REGLA ADR-002: `instalable_en_caja: true` exige `certificacion` en {cULus, cETL, CSA}. Mientras la
# certificacion sea `null`, generador/validar.py rechaza el uso del dispositivo en un archivo de
# cliente. Es el comportamiento deseado: obliga a verificar antes de comprar.
#
# REGLA ADR-003: `control_local_sin_nube` debe ser true en todo dispositivo de este archivo.
# Lo que no cumpla vive en catalogo/excluidos.yaml.
#
# REGLA ADR-004: ningun dispositivo de este catalogo tiene funcion de seguridad de vida. Los sensores
# de calidad de aire lo niegan explicitamente en `notas`.
#
# Fuente de siembra: docs/fuente/Smart-Home-Business-Plan-ON-QC.docx, capitulo 6.
#
# Esquema por dispositivo:
#   id, categoria, fabricante, pais_fabricante, modelo, protocolo, tension, instalable_en_caja,
#   certificacion, ised, control_local_sin_nube, disponibilidad_canada, proveedores,
#   precio_lista_cad, precio_distribuidor_cad, paquetes, notas, fuente_url, verificado
#
# CAMPOS ADICIONALES DE LA CATEGORIA `camara`:
#   substream_bitrate_mbps  bitrate real del sub-stream, medido en banco por modelo y firmware
#   substream_resolucion    resolucion y cadencia del sub-stream, del tipo "640x480@5"
#
# Existen porque el sub-stream es un PARAMETRO DE DISENO, no un valor heredado de la camara:
# determina si el minimo de subida publicado para el paquete se sostiene con los visores
# concurrentes prometidos. herramientas/calc_ancho_banda.py los lee de aqui, no de una constante.
# Mientras esten en `null` y el archivo de cliente no los declare, generador/validar.py rechaza el
# cliente: no se promete visionado remoto simultaneo sobre un numero que nadie ha medido.
# Ver docs/POR-VERIFICAR.md, fila M-13.
---

# =====================================================================================
# ILUMINACION
# =====================================================================================
```
