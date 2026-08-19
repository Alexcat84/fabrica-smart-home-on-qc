# Sustituir una camara

## Cuando

Averia, cambio de modelo, o reubicacion que cambia el campo de vision.

## Antes de ir

- [ ] Revisar el registro: si la camara caia **de noche y con frio**, sospechar del presupuesto PoE
      antes que de la camara. El infrarrojo nocturno y el calefactor tiran a la vez y solo en
      invierno. Ejecutar `python herramientas/calc_poe.py clientes/<cliente>/cliente.yaml` antes de
      cambiar hardware que probablemente esta bien.
- [ ] Confirmar el modelo de repuesto en el catalogo y su rango de temperatura de operacion.
- [ ] Para Reolink: **verificar el soporte de RTSP y ONVIF del modelo y su firmware concretos**.
      Varia dentro de la misma linea.

## Procedimiento

1. Instantanea del controlador.
2. Anotar del as-built: IP, MAC, puerto de switch, etiqueta de cable, zonas y mascaras.
3. Sustituir fisicamente. Reutilizar la misma etiqueta de cable y el mismo puerto.
4. En la camara nueva, **antes de conectarla a la red del cliente**:
   - eliminar la cuenta por defecto y crear la del proyecto,
   - deshabilitar servicios sin uso, funciones de nube y punto a punto,
   - deshabilitar el audio salvo que el cliente lo haya pedido expresamente,
   - actualizar el firmware,
   - guardar la credencial en el baul del cliente.
5. Fijar la IP estatica dentro de `10.<octeto>.30.0/24`, la misma que tenia.
6. Actualizar `mac` y, si cambia, `bitrate_principal_mbps` y `bitrate_substream_mbps` en el archivo
   de variables.
7. Regenerar y desplegar.
8. Reconstruir zonas y mascaras: **el campo de vision del modelo nuevo casi nunca coincide** con el
   anterior, y unas mascaras heredadas dejan la via publica dentro del analisis de movimiento.

## Comprobacion final

- [ ] Graba en el stream principal y detecta en el sub-stream.
- [ ] La hora es correcta (servidor de hora del segmento de camaras).
- [ ] **La camara no puede originar conexiones**: comprobar la regla direccional, no solo que "el
      video se ve".
- [ ] Recalcular almacenamiento si cambio el bitrate: `python generador/validar.py ...`.
- [ ] Actualizar el as-built y entregar la version nueva al cliente.
