# Aplicar una actualizacion, con su reversion

Un stack de codigo abierto sin gestionar se degrada, y el cliente atribuye la degradacion al
instalador con independencia de quien tomara la decision. Por eso las versiones van fijadas y las
actualizaciones automaticas estan deshabilitadas (ADR-006).

## Politica

| Clase | Cadencia |
|---|---|
| Parches de seguridad del sistema operativo | Dias desde la publicacion, tras validar en banco |
| Controlador y complementos | Revision mensual, aplicacion trimestral, salvo que la seguridad obligue |
| Firmware de dispositivo | Solo si corrige un defecto que nos afecta o cierra una vulnerabilidad. **Nunca por si mismo** |

## 1. En el banco de la empresa, nunca en casa del cliente

1. Leer las notas de version **completas**, buscando cambios incompatibles en las integraciones que
   tenemos desplegadas.
2. Aplicar en la instalacion de banco.
3. Probar: luces, clima, camaras, deteccion, notificaciones, tunel e interruptor de soporte.
4. Marcar las instalaciones con integraciones afectadas, para avisarlas por adelantado.

## 2. Preparar al cliente

1. Avisar con antelacion. Ventana acordada, no sorpresa.
2. **Instantanea completa antes de tocar nada.** Sin instantanea no se actualiza, sin excepcion.
3. Confirmar que el ultimo respaldo esta verificado.

## 3. Aplicar

1. Actualizar `version_fijada` en `datos-maestros/software-cliente.yaml` o en el archivo de variables del cliente.
2. Regenerar y desplegar con ansible.
3. Repetir la bateria de pruebas en la instalacion del cliente.

## 4. Si algo falla: revertir

**Antes de aplicar nada a un cliente, el ensayo de reversion de `docs/BANCO.md` seccion 3.2.1 tiene
que estar hecho para ese conjunto de versiones.** Ese ensayo responde a una pregunta distinta de la
restauracion: si la actualizacion va mal, ¿se puede deshacer **sin perder los datos generados desde
que se aplico**? Restaurar un respaldo tambien deshace, pero se lleva por delante los eventos de
camara y el historico de la ventana, y eso hace que en la practica nadie quiera revertir.

Si el ensayo dijo que un componente **no se puede revertir** sin restaurar respaldo, su actualizacion
exige ventana acordada con el cliente y aviso previo: el coste de equivocarse es mucho mayor.


1. Restaurar la instantanea previa.
2. Confirmar que el sistema vuelve al estado anterior.
3. Registrar **que** fallo y **por que**. Esa nota es lo que evita repetir el fallo en el resto de la
   flota.
4. Dejar la version fijada donde estaba hasta entender el problema.

## 5. Al terminar

- [ ] Version anotada en el registro de servicio del cliente.
- [ ] Cambios en la orden de trabajo.
- [ ] Si aparecio un problema, la correccion se aplica a **toda la flota por regeneracion**, no
      cliente a cliente a mano.

## Clientes sin plan de cuidado

Version congelada en la entrega. Ver `congelar-version-cliente.md`.
