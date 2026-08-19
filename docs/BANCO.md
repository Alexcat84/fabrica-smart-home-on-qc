# El banco de la empresa

El banco es una instalacion completa, permanente, en el taller, que **no pertenece a ningun cliente**.
Existe para que ninguna decision tecnica se tome por primera vez en casa de alguien.

Este documento se escribe **antes** que los roles de ansible, a proposito. Un rol escrito sin banco es
una suposicion con sintaxis YAML: parece infraestructura como codigo y en realidad nadie lo ha
ejecutado nunca. La idempotencia, el tiempo de reconstruccion y la compatibilidad entre versiones son
propiedades que se **miden**, no que se declaren.

---

## 1. Que responde el banco

Cuatro preguntas, y ninguna se puede responder sin el:

1. **¿Este rol es idempotente?** Ejecutarlo dos veces seguidas no debe cambiar nada la segunda vez.
2. **¿Se reconstruye en menos de cuatro horas?** Es el objetivo declarado en el contrato del cliente,
   en `runbooks/restaurar-controlador.md` y en el as-built. Sin cronometrarlo, es una frase.
3. **¿Esta actualizacion rompe algo?** Antes de tocar a un cliente, se aplica aqui.
4. **¿Que version fijamos?** Las 27 `version_fijada` de `catalogo/software.yaml` salen de lo que
   quede corriendo aqui, no de la ultima etiqueta publicada upstream.

---

## 2. Hardware minimo

El banco tiene que **parecerse al peor cliente que vendemos**, no al mejor. Si funciona en el
equivalente a un paquete M reacondicionado, funciona en todo lo demas.

### 2.1 Controlador

| Elemento | Minimo | Por que |
|---|---|---|
| Equipo | Micro escritorio empresarial reacondicionado, de una de las tres familias del catalogo | Es lo que se instala. Probar en un portatil moderno oculta problemas de decodificacion |
| Procesador | Intel con graficos integrados, de la **generacion mas antigua** que se este comprando | La inferencia por OpenVINO y la decodificacion por hardware dependen de la generacion. Ver M-04 |
| RAM | 16 GB | El minimo del paquete M. Si el stack no cabe en 16 GB, hay que saberlo aqui |
| Disco de sistema | NVMe 250 a 500 GB | Igual que en produccion |
| Disco de vigilancia | Un disco de vigilancia real, aunque sea de poca capacidad | Un SSD de consumo esconde el comportamiento de escritura continua |

Conviene tener **dos** controladores identicos: uno estable con la version desplegada en la flota, y
otro para probar la siguiente. Sin el segundo, cada prueba de actualizacion deja el banco inservible
hasta terminar.

### 2.2 Red

| Elemento | Minimo | Por que |
|---|---|---|
| Pasarela | La misma familia que se instala, con VLAN y cortafuegos con estado | La matriz direccional de `plantillas/red/firewall.yaml.j2` hay que aplicarla de verdad, no leerla |
| Switch PoE+ | 8 puertos, presupuesto PoE conocido | Permite comprobar el calculo de `calc_poe.py` contra consumo medido |
| Punto de acceso | Uno, con multiples SSID mapeados a VLAN | Comprobar que la gestion no queda expuesta por radio |
| Octeto reservado | `10.98.x.0/24` | El 99 es del cliente de demostracion. El banco necesita el suyo para que la superposicion de soporte no colisione |

### 2.3 Radio y camaras

| Elemento | Minimo | Por que |
|---|---|---|
| Coordinador Zigbee | Uno, por Ethernet, igual que en produccion | La ruta USB tiene otros modos de falla |
| Dispositivos Zigbee | Al menos un interruptor de red, un dimmer, un termostato y un sensor de bateria | Sin un dispositivo alimentado de red no se puede probar el orden de emparejamiento |
| Camaras | **Una por cada familia del catalogo que se venda.** Es el punto que mas se escatima y el que mas caro sale | Sin ellas no se pueden cerrar M-02, M-03 ni M-13 |
| UPS | Uno con puerto de datos | Network UPS Tools y el apagado ordenado hay que probarlos |

### 2.4 Lo que el banco necesita y no es hardware

- **Un enlace a internet con subida limitable**, o una forma de estrangularla. Los dos escenarios de
  `calc_ancho_banda.py` hay que verlos fallar de verdad, no solo calcularlos.
- **Una caja de interruptor sin neutro**, montada en un panel de pruebas. Es la rama 2 del arbol de
  ADR-008 y no se puede probar en una pared moderna.
- **Lamparas LED de los modelos que se supongan**, para fijar rangos de atenuacion y detectar
  parpadeo antes de descubrirlo en el salon de un cliente.

---

## 3. Que se prueba, y como se da por bueno

### 3.1 Idempotencia de cada rol

Requisito de aceptacion de **todo** rol de `ansible/roles/`, sin excepcion:

```bash
# Primera pasada: sobre un sistema recien instalado.
ansible-playbook -i ansible/inventario/banco.yml \
    ansible/playbooks/aprovisionar-controlador.yml --tags <rol>

# Segunda pasada, inmediatamente despues.
ansible-playbook -i ansible/inventario/banco.yml \
    ansible/playbooks/aprovisionar-controlador.yml --tags <rol>
```

**Criterio de aceptacion: `changed=0` en la segunda pasada.** Un solo `changed` es un defecto del rol,
no una peculiaridad del sistema. Los sospechosos habituales son las tareas que escriben un archivo
con marca de tiempo, las que usan `command` sin `creates` o `changed_when`, y las que reinician un
servicio incondicionalmente.

Se registra por rol:

| Rol | Fecha | `changed` en 2.a pasada | Notas |
|---|---|---|---|
| `base` | | | |
| `docker` | | | |
| `red` | | | |
| `mosquitto` | | | |
| `zigbee2mqtt` | | | |
| `homeassistant` | | | |
| `frigate` | | | |
| `soporte_remoto` | | | |
| `backup` | | | |
| `monitorizacion` | | | |

### 3.2 Restauracion completa cronometrada

Se ejecuta `runbooks/restaurar-controlador.md` **entero**, con cronometro, contra el objetivo de
cuatro horas. No es una lectura del runbook: es borrar el disco del controlador de banco y
reconstruirlo.

Se mide por tramo, porque el total no dice donde esta el problema:

| Tramo | Objetivo | Medido | Notas |
|---|---|---|---|
| 1. Preparar el anfitrion | 45 min | | |
| 2. Regenerar desde plantilla | 5 min | | |
| 3. Aprovisionar el stack | 60 min | | |
| 4. Restaurar los datos | 45 min | | |
| 5. Reconectar la malla Zigbee | 20 min | | |
| 6. Comprobacion | 30 min | | |
| **Total** | **< 4 h** | | |

**Regla:** si el total pasa de cuatro horas, el defecto esta en la plantilla, en el rol o en el
runbook. Se corrige **ahi** y se vuelve a cronometrar. No se anota el tiempo real y se sigue: eso
convierte un compromiso contractual en una aspiracion.

Frecuencia: al cerrar cada version fijada, y como minimo una vez al ano.

### 3.3 Validacion de cada actualizacion antes de tocar a un cliente

Ningun cliente recibe una version que no haya corrido aqui primero. Secuencia:

1. Leer las notas de version **completas**, buscando cambios incompatibles en las integraciones
   desplegadas.
2. Instantanea del controlador de banco de pruebas.
3. Aplicar la actualizacion **solo en el banco de pruebas**, no en el estable.
4. Bateria de pruebas de aceptacion (seccion 3.4).
5. Dejarla corriendo **al menos una semana**. Los fallos de integracion Zigbee y las fugas de memoria
   no aparecen en diez minutos.
6. Si pasa: se actualiza `version_fijada`, se anota la fecha, y entra en la ventana de
   `runbooks/aplicar-actualizacion.md` para la flota.
7. Si no pasa: se registra **que** fallo y **por que**. Esa nota vale mas que la actualizacion, porque
   evita repetir el intento en seis meses.

### 3.4 Bateria de pruebas de aceptacion del banco

La misma que el cliente firma en el acta, mas lo que el cliente no ve:

- [ ] Las luces responden desde la pared con el controlador apagado
- [ ] El sistema opera con el enlace de internet desconectado
- [ ] El UPS toma el relevo y el apagado ordenado ocurre
- [ ] Escaneo externo de puertos limpio
- [ ] Acceso remoto por el tunel desde fuera de la red del banco
- [ ] La camara **no puede originar** conexiones; el grabador si la alcanza
- [ ] El interruptor de soporte expira solo, y **tambien al reiniciar**
- [ ] Respaldo, verificacion de integridad y restauracion de un archivo
- [ ] Deteccion de persona en cada camara, con la notificacion de contenido minimo
- [ ] `python herramientas/verificar_todo.py` en verde contra el estado del banco

---

## 4. Procedimiento para fijar las 27 versiones

`catalogo/software.yaml` tiene 27 componentes con `version_fijada: null` (fila B-04). Se fijan **a
partir de lo que quede corriendo en el banco**, no de la ultima etiqueta publicada upstream.

### 4.1 Por que no se fija la ultima version

Porque la ultima version de cada componente no ha convivido con las otras veintiseis. Lo que se fija
es un **conjunto que se ha visto funcionar junto durante una semana**, que es una propiedad distinta y
mas util que la de estar al dia.

### 4.2 Procedimiento

1. **Partir de un banco limpio.** Instalacion completa desde `aprovisionar-controlador.yml`, sin
   arrastrar estado de pruebas anteriores.
2. **Anotar la version efectivamente desplegada de cada componente.** No la que pedimos: la que quedo.
   Para contenedores, el digest, no la etiqueta: las etiquetas se mueven.

   ```bash
   docker inspect --format '{{index .RepoDigests 0}}' <contenedor>
   ```

3. **Dejarlo correr una semana** con las camaras grabando, la malla Zigbee poblada y el respaldo
   ejecutandose a diario. Es el unico periodo en que aparecen la fuga de memoria, el disco que se
   llena y el dispositivo que se cae del arbol Zigbee cada tres dias.
4. **Ejecutar la bateria de aceptacion** de la seccion 3.4.
5. **Ejecutar la restauracion cronometrada** de la seccion 3.2 sobre ese conjunto. Un conjunto que no
   se puede reconstruir en cuatro horas no se fija, por bien que funcione.
6. **Escribir las 27 versiones** en `catalogo/software.yaml`, y con ellas:
   - `version_fijada`, con el digest cuando aplique,
   - la fecha de fijacion en `notas`,
   - cerrar la fila B-04 y anotarla en el registro de `POR-VERIFICAR.md`.
7. **Etiquetar el commit** con el nombre del conjunto, por ejemplo `stack-2026.09`. Es lo que permite
   responder "que tenia este cliente instalado en marzo" sin adivinar.
8. **Registrar el conjunto** en la tabla siguiente.

### 4.3 Registro de conjuntos fijados

| Conjunto | Fecha | Restauracion cronometrada | Componentes | Notas |
|---|---|---|---|---|
| _(ninguno todavia)_ | | | | |

### 4.4 Cadencia

- **Revision mensual** de notas de version, sin aplicar nada.
- **Fijacion trimestral** de un conjunto nuevo, salvo que un problema de seguridad obligue antes.
- **Un cliente sin plan de cuidado se queda en el conjunto que tenia** al no renovar. Ver
  `runbooks/congelar-version-cliente.md`.

---

## 5. Lo que el banco tambien resuelve

Varias filas de `POR-VERIFICAR.md` se cierran aqui y no en otro sitio:

| Fila | Que se mide en el banco |
|---|---|
| **A-08** | Operacion sin neutro del Inovelli Blue 2-1, y **a partir de que carga exige bypass**, sobre el panel de pruebas con lampara LED real |
| **A-02** | Ruta de control local de Lutron Caseta, con el banco **desconectado de internet**. Es la unica prueba que vale |
| **M-02** | RTSP y ONVIF de cada modelo de Reolink, con su firmware |
| **M-04** | Generacion de procesador que soporta OpenVINO y decodificacion por hardware |
| **M-11** | Que funciones de ecobee sobreviven sin la nube del fabricante |
| **M-13** | **Bitrate y resolucion reales del sub-stream**, por modelo y firmware. Se mide con el enlace estrangulado, comprobando los dos escenarios de `calc_ancho_banda.py` |
| **B-04** | Las 27 versiones, por el procedimiento de la seccion 4 |

Cerrar esas siete filas es, en la practica, el primer trabajo del banco.
