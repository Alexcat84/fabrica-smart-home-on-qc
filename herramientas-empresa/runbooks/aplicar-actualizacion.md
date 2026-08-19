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

## 0. PASO PREVIO OBLIGATORIO: ¿migra el esquema del recorder?

**Esto va antes que nada, incluida la instantanea** (ADR-013).

Leer las notas de version y determinar si la actualizacion **migra el esquema de la base de datos del
`recorder`**. La migracion es unidireccional: al arrancar la version nueva, la base se transforma y la
version anterior ya no la puede leer. Revertir el binario deja al sistema con una base ilegible.

La misma pregunta vale para cualquier componente con estado migrado -base de Zigbee, indice del
grabador-: **¿la version anterior puede leer lo que escribio la nueva?**

De la respuesta salen dos rutas, y **no se empieza sin saber cual es**:

| | **RUTA A — sin migracion** | **RUTA B — con migracion** |
|---|---|---|
| Reversion | Existe | **No existe** |
| Mecanismo | Volver al binario o imagen anterior | Restaurar respaldo |
| Criterio de datos | **Cero perdidos** | **Perdida declarada**, no cero |
| Rodaje en banco | Opcional | **Obligatorio** |
| Ventana con el cliente | Recomendada | **Obligatoria, acordada por adelantado** |
| Que se le dice al cliente antes | Que hay ventana | **Cuanto historial va a perder, calculado** |

Ruta anotada en la orden de trabajo antes de continuar: ______

---

## 1. En el banco de la empresa, nunca en casa del cliente

1. Leer las notas de version **completas**, buscando cambios incompatibles en las integraciones que
   tenemos desplegadas.
2. Aplicar en la instalacion de banco.
3. Probar: luces, clima, camaras, deteccion, notificaciones, tunel e interruptor de soporte.
4. Marcar las instalaciones con integraciones afectadas, para avisarlas por adelantado.

## 2. Preparar al cliente

1. Avisar con antelacion. Ventana acordada, no sorpresa.
2. **Instantanea completa antes de tocar nada.** Sin instantanea no se actualiza, sin excepcion.
   En **ruta B**, ademas: respaldo verificado con la **hora exacta anotada**, y calculo del historial
   que se perderia si hubiera que restaurar. Esa cifra se le dice al cliente **antes** de aplicar.
3. Confirmar que el ultimo respaldo esta verificado.

## 3. Aplicar

1. Actualizar `version_fijada` en `datos-maestros/software-cliente.yaml` o en el archivo de variables del cliente.
2. Regenerar y desplegar con ansible.
3. Repetir la bateria de pruebas en la instalacion del cliente.

## 4. Si algo falla: deshacer

**Antes de aplicar nada a un cliente, el ensayo de `docs/BANCO.md` seccion 3.2.1 tiene que estar
hecho para ese conjunto de versiones**, por la ruta que corresponda.

### Ruta A: revertir

Volver al binario o imagen anterior. **Cero datos perdidos**, y el ensayo lo ha medido.

1. Revertir al artefacto anterior.
2. Confirmar que el sistema vuelve al estado previo.
3. **Comprobar que los datos generados desde la actualizacion siguen ahi.**
4. Registrar que fallo y por que.

### Ruta B: restaurar, con perdida declarada

La reversion no existe: la migracion del esquema es unidireccional. La unica via es restaurar el
respaldo previo, y **eso pierde el historial desde ese punto**.

1. Restaurar el respaldo tomado antes de la actualizacion.
2. Confirmar que el sistema vuelve al estado previo.
3. **Anotar el hueco real**: cuanto historial se ha perdido, en horas o dias.
4. **Decirselo al cliente**, con la cifra. Ya se le habia dicho el rango antes de aplicar; ahora se
   le dice el dato.
5. Registrar que fallo, por que, y el volumen perdido, en el registro de servicio. A los dos anos,
   "por que falta el historico de marzo" tiene respuesta.


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
