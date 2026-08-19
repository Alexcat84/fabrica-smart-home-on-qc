# Congelar la version de un cliente que no renueva

## Por que este runbook existe

Este es el momento en que un negocio de integracion se rompe en silencio: el cliente deja de pagar
el plan de cuidado, el sistema sigue funcionando, y catorce meses despues llama porque "algo se ha
roto". Si no hay una frontera escrita, esa llamada es trabajo no pagado y una discusion incomoda.

La frontera se traza **ahora**, por escrito, y con el sistema en un estado conocido.

## Procedimiento

1. **Aviso por escrito**, antes de la fecha de no renovacion, explicando que:
   - el sistema seguira funcionando exactamente igual que hoy,
   - las versiones quedan congeladas en el estado actual,
   - las actualizaciones pasan a ser responsabilidad del cliente,
   - el acceso de soporte deja de estar disponible salvo contratacion puntual.

2. **Congelar versiones.** Fijar `version_fijada` de todo componente al valor desplegado hoy, en el
   archivo de variables del cliente. Nada de etiquetas moviles.

3. **Ultimo respaldo verificado**, con prueba de restauracion incluida si toca por calendario.

4. **Regenerar y entregar el paquete completo**, con el as-built al dia.

5. **Entregar el baul de credenciales** y confirmar que el cliente puede abrirlo sin nosotros.

6. **Retirar el acceso de la empresa de forma permanente**, con el procedimiento documentado, y
   dejar constancia escrita de que se ha hecho.

7. **Entregar la seccion de continuidad** del as-built, que explica a otro proveedor como tomar el
   relevo: que hay instalado, como esta direccionado, donde estan las credenciales, como se respalda
   y como se restaura.

## Que se le entrega, en una lista

- [ ] Documento as-built completo y actualizado, en su idioma.
- [ ] Baul de credenciales, con procedimiento de recuperacion administrativa.
- [ ] Procedimiento de respaldo y restauracion.
- [ ] Apendice de licencias del software desplegado.
- [ ] Aviso escrito de version congelada, con la lista de versiones.
- [ ] Confirmacion escrita de retirada del acceso de la empresa.

## Lo que NO se hace

- No se degrada el sistema.
- No se deja una bomba de relojeria ni una dependencia oculta que obligue a volver.
- No se retiene informacion que el cliente necesitaria para que otro se hiciera cargo.

Un cliente que se va bien documentado vuelve, o recomienda. Uno que se va atrapado, no.
