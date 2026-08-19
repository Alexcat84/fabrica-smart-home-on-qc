# Restaurar un controlador

**Objetivo declarado y contractual: reconstruccion completa desde plantilla mas respaldo en MENOS DE
CUATRO HORAS, sin conocimiento tribal.**

Este runbook se ejecuta de verdad al menos una vez al ano como prueba de restauracion del plan de
cuidado, aunque no haya pasado nada. Un respaldo que nadie ha restaurado nunca no es un respaldo: es
una suposicion.

Si la ejecucion tarda mas de cuatro horas, **el defecto esta en la plantilla, en el rol de ansible o
en este runbook**. Se corrige ahi. No se anota el tiempo y se sigue.

## Lo que se recupera y lo que no

| Se recupera | No se recupera |
|---|---|
| Configuracion de Home Assistant, automatizaciones, paneles | **El video grabado** |
| Base de la red Zigbee, con emparejamientos y clave de red | |
| Configuracion del grabador, zonas y mascaras | |
| Baul de credenciales | |
| Exportaciones de configuracion de red | |

El video se protege solo por redundancia de disco, y solo en los niveles que la incluyen. El cliente
lo sabe: consta en el acta de aceptacion que firmo.

## Necesitas antes de empezar

- [ ] Acceso fisico, o una sesion de soporte abierta por el cliente.
- [ ] La **clave de cifrado del respaldo**, que esta en poder del cliente. Sin ella el respaldo es
      irrecuperable, y eso tambien consta por escrito.
- [ ] El archivo de variables del cliente, en este repositorio.
- [ ] Hardware de repuesto de la misma familia (OptiPlex Micro, ThinkCentre Tiny o EliteDesk Mini).

## Procedimiento

### 1. Preparar el anfitrion (unos 45 min)

```bash
ansible-playbook -i ansible/inventario/<cliente>.yml \
    ansible/playbooks/aprovisionar-controlador.yml --tags base
```

### 2. Regenerar la configuracion desde plantilla (unos 5 min)

```bash
python generador/validar.py clientes/<cliente>/cliente.yaml
python generador/generar.py clientes/<cliente>/cliente.yaml
```

Si `validar.py` falla, **para y corrige**. Un paquete generado desde un cliente invalido parece
correcto y no lo es.

### 3. Aprovisionar el stack (unos 60 min)

```bash
ansible-playbook -i ansible/inventario/<cliente>.yml \
    ansible/playbooks/aprovisionar-controlador.yml
```

Versiones **fijadas**. No se aprovecha la reconstruccion para actualizar: se restaura a la version
que el cliente tenia, y las actualizaciones se aplican despues, deliberadamente y con su propia
ventana.

### 4. Restaurar los datos (unos 45 min)

```bash
restic -r <destino> restore latest --target /
# o, con Borg:
borg extract <destino>::<archivo>
```

Restaurar en este orden: baul de credenciales, base de Zigbee, configuracion de Home Assistant,
configuracion del grabador.

### 5. Reconectar la malla Zigbee (unos 20 min)

La base de Zigbee2MQTT incluye la clave de red y los emparejamientos: **los dispositivos vuelven
solos** si se restaura ANTES de arrancar el coordinador.

Si se arranca el coordinador con la base vacia, se genera una red nueva y hay que reemparejar a mano
todos los dispositivos, uno por uno, muchos de ellos detras de una placa atornillada. Ese es
exactamente el error que convierte cuatro horas en dos dias.

### 6. Comprobacion (unos 30 min)

- [ ] Las luces responden desde la pared **y** desde la interfaz.
- [ ] Los termostatos leen temperatura y aceptan consigna.
- [ ] Las camaras graban y detectan.
- [ ] El tunel de acceso remoto levanta desde red celular, no solo desde la red de casa.
- [ ] **El interruptor de soporte esta apagado** y su temporizador cancelado.
- [ ] El respaldo vuelve a ejecutarse y su verificacion de integridad pasa.
- [ ] Checklist de endurecimiento de `docs/SEGURIDAD.md` completo.
- [ ] Escaneo externo de puertos limpio.

## Al terminar

- Anotar el **tiempo total real** en el registro de servicio.
- Anotar toda incidencia y **corregirla en la plantilla**, no en el anfitrion.
- Entregar al cliente el documento as-built regenerado.
