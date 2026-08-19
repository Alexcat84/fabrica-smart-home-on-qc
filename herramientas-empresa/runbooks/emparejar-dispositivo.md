# Emparejar un dispositivo

## Antes de empezar

- [ ] El dispositivo esta en `datos-maestros/dispositivos/`. Si no esta, **para**: se evalua primero
      contra las reglas de seleccion y se anade al catalogo o al registro de exclusion.
- [ ] Si va dentro de una caja electrica: **verificar la marca cULus, cETL o CSA impresa en la unidad
      fisica**. No en la factura, no en la web del fabricante. En la unidad. Sin marca, se rechaza y
      se devuelve.
- [ ] El dispositivo esta anadido al archivo de variables del cliente y `validar.py` pasa limpio.

## Orden de emparejamiento (importa mucho)

**Primero todos los dispositivos alimentados de red, despues los de bateria.** Los alimentados de red
actuan como routers de la malla; si emparejas un sensor de bateria antes de que la malla exista,
elige mal padre y arrastra ese problema hasta que lo vuelvas a emparejar. Es la causa mas comun de
"el sensor del sotano se desconecta a veces".

## Procedimiento

1. Abrir el emparejamiento **solo el tiempo necesario**:
   `permit_join` a `true` en Zigbee2MQTT, o el boton de la interfaz.
2. Poner el dispositivo en modo emparejamiento segun su manual.
3. Confirmar que aparece con su direccion IEEE.
4. **Cerrar el emparejamiento inmediatamente.** Dejarlo abierto permite que cualquiera con un
   dispositivo Zigbee se una a la red de la casa.
5. Renombrar segun `docs/NOMENCLATURA.md`: `<categoria>_<area>_<discriminador>`.
   Comprobar que el nombre no contiene ningun termino vetado (seccion 1 del documento).
6. Anotar la IEEE real en el archivo de variables del cliente, sustituyendo
   `CAMBIAR-EN-COMISIONAMIENTO`.
7. Regenerar: `python herramientas-empresa/generador/generar.py clientes/<cliente>/cliente.yaml`.
8. Si es un atenuador: fijar minimo y maximo de atenuacion para **ese circuito** con la lampara real
   instalada. La mayoria de quejas de parpadeo o zumbido son incompatibilidad con la lampara LED, no
   averia del dispositivo, y se resuelven aqui.
9. Si es un control de ventilador: **confirmar que el SKU esta clasificado para carga de motor**.
   Un atenuador de iluminacion sobre un motor de ventilador es riesgo de incendio y de averia del
   motor. No se hace nunca.

## Comprobacion final

- [ ] El dispositivo responde desde la interfaz del sistema.
- [ ] **Responde desde el interruptor de pared con el controlador apagado** (regla de respaldo
      mecanico). Si no, el diseno esta mal, no la instalacion.
- [ ] Aparece en el documento as-built regenerado, con su area y su circuito.
- [ ] Registrado en la orden de trabajo.
