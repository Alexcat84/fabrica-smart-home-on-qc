# El banco de la empresa

El banco es una instalacion completa, permanente, en el taller, que **no pertenece a ningun cliente**.
Existe para que ninguna decision tecnica se tome por primera vez en casa de alguien.

Este documento se escribe **antes** que los roles de ansible, a proposito. Un rol escrito sin banco es
una suposicion con sintaxis YAML: parece infraestructura como codigo y en realidad nadie lo ha
ejecutado nunca. La idempotencia, el tiempo de reconstruccion y la compatibilidad entre versiones son
propiedades que se **miden**, no que se declaren.

---

## 1. Que responde el banco

Cinco preguntas, y ninguna se puede responder sin el:

1. **¿Este rol es idempotente?** Ejecutarlo dos veces seguidas no debe cambiar nada la segunda vez.
2. **¿Se reconstruye en menos de cuatro horas?** Es el objetivo declarado en el contrato del cliente,
   en `herramientas-empresa/runbooks/restaurar-controlador.md` y en el as-built. Sin cronometrarlo, es una frase.
3. **¿Esta actualizacion rompe algo?** Antes de tocar a un cliente, se aplica aqui.
4. **¿Se puede DESHACER esta actualizacion sin perder datos?** Pregunta distinta de la 2, y la que
   ocurre de verdad. Ver la seccion 3.2.1.
5. **¿Que version fijamos?** Las `version_fijada` de `datos-maestros/software-cliente.yaml` y de
   `software-empresa.yaml` salen de lo que quede corriendo aqui, no de la ultima etiqueta publicada
   upstream.

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
| Pasarela | La misma familia que se instala, con VLAN y cortafuegos con estado | La matriz direccional de `producto-cliente/stack/red/firewall.yaml.j2` hay que aplicarla de verdad, no leerla |
| Switch PoE+ | 8 puertos, presupuesto PoE conocido | Permite comprobar el calculo de `calc_poe.py` contra consumo medido |
| Punto de acceso | Uno, con multiples SSID mapeados a VLAN | Comprobar que la gestion no queda expuesta por radio |
| Octeto reservado | `10.98.x.0/24` | El 99 es del cliente de demostracion. El banco necesita el suyo para que la superposicion de soporte no colisione |

### 2.2.1 Sin este hardware, tres roles NO son validables

Dicho sin rodeos, para que nadie escriba esos roles "provisionalmente" y de por hecho que ya estan:

| Rol | Hardware imprescindible | Sin el |
|---|---|---|
| `zigbee2mqtt` | **Coordinador Zigbee por Ethernet o PoE**, mas al menos un dispositivo alimentado de red y uno de bateria | No se puede probar el orden de emparejamiento, que es la causa numero uno de "el sensor del sotano se desconecta a veces". La ruta USB tiene otros modos de falla y probar en ella no dice nada de la de produccion |
| `frigate` | **Dos camaras PoE de modelos distintos** y el switch PoE+ | No se puede cerrar M-02 (RTSP y ONVIF varian por modelo y firmware), ni M-13, ni M-14. Con una sola camara no hay nada que comparar |
| `red` | **Switch PoE+ gestionado** con 802.1Q y presupuesto PoE publicado | La matriz direccional de cortafuegos no se aplica de verdad, solo se lee. Y `calc_poe.py` no se puede contrastar contra consumo medido |

**Un rol escrito sin ese hardware es una suposicion con sintaxis YAML.** No se marca como hecho en la
tabla de la seccion 3.1 hasta que alguien lo haya ejecutado dos veces y visto `changed=0`.

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

Requisito de aceptacion de **todo** rol de `herramientas-empresa/ansible/roles/`, sin excepcion:

```bash
# Primera pasada: sobre un sistema recien instalado.
ansible-playbook -i herramientas-empresa/ansible/inventario/banco.yml \
    herramientas-empresa/ansible/playbooks/aprovisionar-controlador.yml --tags <rol>

# Segunda pasada, inmediatamente despues.
ansible-playbook -i herramientas-empresa/ansible/inventario/banco.yml \
    herramientas-empresa/ansible/playbooks/aprovisionar-controlador.yml --tags <rol>
```

**Criterio de aceptacion: `changed=0` en la segunda pasada.** Un solo `changed` es un defecto del rol,
no una peculiaridad del sistema. Los sospechosos habituales son las tareas que escriben un archivo
con marca de tiempo, las que usan `command` sin `creates` o `changed_when`, y las que reinician un
servicio incondicionalmente.

**Estado por rol.** Las tres columnas dicen lo que hay que saber antes de escribir una linea: si el
banco actual permite validarlo, que falta si no, y que hay que ver para darlo por bueno.

| Rol | Validable en banco actual | Hardware que falta | Criterio de aceptacion |
|---|---|---|---|
| `base` | **Si** | — | `changed=0` en 2.a pasada. SSH sin contrasena, cortafuegos denegando entrante, actualizaciones desatendidas apagadas |
| `docker` | **Si** | — | `changed=0`. Versiones fijadas por digest, no por etiqueta |
| `red` | **No** | Switch PoE+ gestionado con 802.1Q; pasarela con cortafuegos con estado | `changed=0`. Matriz direccional aplicada y **probada**: la camara no origina conexiones y Controller no alcanza Management |
| `mosquitto` | **Si** | — | `changed=0`. `allow_anonymous false`, ACL por privilegio minimo, conexion anonima rechazada |
| `zigbee2mqtt` | **No** | **Coordinador Zigbee por Ethernet**, un dispositivo de red y uno de bateria | `changed=0`. Emparejamiento cerrado por defecto. Orden de emparejamiento probado: el de bateria se une a traves de una malla ya madura |
| `homeassistant` | Parcial | Depende de `zigbee2mqtt` y `frigate` para la prueba completa | `changed=0`. Paquetes por dominio cargados, panel renderizado, interruptor de soporte con sus cuatro revocaciones |
| `frigate` | **No** | **Dos camaras PoE de modelos distintos**, switch PoE+ | `changed=0`. Grabacion sobre principal, deteccion sobre sub, apertura sobre medio. Inferencia por iGPU sin transcodificar (ADR-012) |
| `soporte_remoto` | **Si** | — | `changed=0`. Revocacion probada en las cuatro rutas, **incluida la de reinicio** |
| `backup` | **Si** | — | `changed=0`. Respaldo cifrado, verificacion de integridad, y **restauracion de un archivo comprobada** |
| `monitorizacion` | Parcial | UPS con puerto de datos; camaras para las comprobaciones de disponibilidad | `changed=0`. NUT reporta estado y ejecuta apagado ordenado |

Tres roles marcados **No** y dos **Parcial**. Esa es la razon de que los ocho roles vacios sigan
vacios, y de que la cotizacion del banco sea el camino critico del trabajo tecnico.

Al validar cada uno se rellena tambien:

| Rol | Fecha | `changed` en 2.a pasada | Reversion probada | Notas |
|---|---|---|---|---|
| `base` | | | | |
| `docker` | | | | |
| `red` | | | | |
| `mosquitto` | | | | |
| `zigbee2mqtt` | | | | |
| `homeassistant` | | | | |
| `frigate` | | | | |
| `soporte_remoto` | | | | |
| `backup` | | | | |
| `monitorizacion` | | | | |

### 3.2 Restauracion completa cronometrada

Se ejecuta `herramientas-empresa/runbooks/restaurar-controlador.md` **entero**, con cronometro, contra el objetivo de
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

### 3.2.1 ENSAYO DE REVERSION

**Criterio separado del de restauracion, y hay que medirlo aparte.** Son dos preguntas distintas:

- **Restauracion** responde a "el controlador ha muerto, ¿puedo reconstruirlo?"
- **Reversion** responde a "he aplicado una actualizacion, va mal, ¿puedo deshacerla **sin** perder
  lo que ha pasado desde entonces?"

La segunda es la que ocurre de verdad, y con diferencia. Restaurar un respaldo para deshacer una
actualizacion funciona, pero **tira por la borda todo lo ocurrido desde el ultimo respaldo**: eventos
de camara, cambios de estado, historico y cualquier ajuste hecho en la ventana. Si la unica forma de
revertir es restaurar, la reversion cuesta datos, y eso hace que nadie quiera revertir. Entonces se
quedan con la version mala y "ya lo miraremos".

**PASO PREVIO OBLIGATORIO (ADR-013)**

Antes de nada, **leer las notas de version y determinar si la actualizacion migra el esquema de la
base de datos del `recorder`**. La migracion es unidireccional: al arrancar la version nueva la base
se transforma, y la anterior ya no la puede leer. De esa respuesta salen dos rutas con criterios
distintos, y no se empieza hasta saber cual es.

| | **RUTA A — sin migracion** | **RUTA B — con migracion** |
|---|---|---|
| Reversion | Existe | **No existe** |
| Mecanismo | Volver al binario o imagen anterior | Restaurar respaldo |
| Criterio de datos | **Cero perdidos** | **Perdida declarada**, no cero |
| Que se mide | Tiempo de reversion | Tiempo de restauracion **y volumen de historial perdido** |
| Rodaje en banco | Opcional | **Obligatorio** |
| Ventana con el cliente | Recomendada | **Obligatoria, acordada por adelantado** |

Se aplica igual a cualquier componente con estado migrado: base de Zigbee, indice del grabador. La
pregunta es siempre la misma: **¿la version anterior puede leer lo que escribio la nueva?**

---

**Procedimiento, RUTA A**

1. Estado de partida: banco estable, con la version fijada de la flota y datos reales de al menos una
   semana de funcionamiento.
2. **Instantanea previa** del anfitrion.
3. Aplicar la actualizacion candidata.
4. Dejarla correr **al menos una hora**, con las camaras grabando y la malla activa, para que se
   generen datos posteriores a la actualizacion.
5. **Revertir**, sin restaurar el respaldo: volver a la version anterior por el mecanismo del propio
   componente -imagen de contenedor anterior, instantanea del anfitrion, o el que corresponda-.
6. Comprobar la bateria de aceptacion de la seccion 3.4.
7. **Comprobar que los datos generados en el paso 4 siguen ahi.** Es el punto entero del ensayo.

**Cronometraje y criterio de aceptacion**

| Medida | Objetivo | Medido | Notas |
|---|---|---|---|
| Tiempo de reversion | **< 30 min** | | Si tarda mas, en una incidencia real nadie va a revertir |
| Datos perdidos | **cero** | | Si se pierden datos, no es reversion: es restauracion con otro nombre |
| Bateria de aceptacion tras revertir | pasa entera | | |
| Reversion posible sin acceso fisico | si | | Una reversion que exige ir a casa del cliente no sirve de noche |

**Procedimiento, RUTA B**

La reversion no existe. Lo que se ensaya es la **restauracion con perdida declarada**, y lo que se
mide es cuanto cuesta y cuanto se pierde.

1. Estado de partida igual que en ruta A, con al menos una semana de datos reales.
2. **Instantanea previa** y respaldo verificado, con la hora exacta anotada.
3. Aplicar la actualizacion candidata.
4. Dejarla correr **al menos una hora**, generando datos posteriores.
5. Restaurar el respaldo del paso 2.
6. Bateria de aceptacion de la seccion 3.4.
7. **Medir el hueco**: cuanto historial hay entre la hora del respaldo y la de la restauracion. Ese
   es el volumen que un cliente perderia en el peor caso.

| Medida | Objetivo | Medido | Notas |
|---|---|---|---|
| Tiempo de restauracion | **< 2 h** | | Es restauracion, no reversion: cuesta mas por definicion |
| Volumen de historial perdido | **declarado** | | En horas o dias. **No se pretende que sea cero** |
| Bateria de aceptacion tras restaurar | pasa entera | | |
| Frecuencia de respaldo suficiente | si/no | | Si el hueco es inaceptable, la respuesta es respaldar mas a menudo antes de la ventana, no aplicar la actualizacion igual |

**En ruta B, el volumen de historial que se va a perder se calcula y se dice al cliente ANTES de
aplicar.** Es la diferencia entre una decision informada y una disculpa.

---

**Regla:** si un componente **no se puede revertir** sin restaurar respaldo -es decir, si cae en ruta
B-, se anota como tal en su fila de la seccion 3.1 y **su procedimiento de actualizacion cambia**:
pasa a exigir ventana acordada con el cliente y aviso previo, porque el coste de equivocarse es mucho
mayor.

Frecuencia: en **cada** conjunto de versiones que se fije, antes de tocar a un cliente. **Ruta B
exige rodaje en banco**; ruta A lo tiene como opcional.

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
   `herramientas-empresa/runbooks/aplicar-actualizacion.md` para la flota.
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
- [ ] `python herramientas-empresa/verificar_todo.py` en verde contra el estado del banco

---

## 4. Procedimiento para fijar las versiones

`datos-maestros/software-cliente.yaml` tiene 27 componentes con `version_fijada: null` (fila B-04). Se fijan **a
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
6. **Escribir las 27 versiones** en `datos-maestros/software-cliente.yaml`, y con ellas:
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
  `herramientas-empresa/runbooks/congelar-version-cliente.md`.

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
| **M-13** | **Bitrate y resolucion reales del sub-stream**, por modelo y firmware |
| **M-14** | **Numero de flujos publicados, y bitrate del flujo MEDIO.** Se mide con el enlace estrangulado, comprobando los TRES escenarios de `calc_ancho_banda.py` (ADR-012). Es lo que decide los minimos publicados de los cuatro paquetes |
| **B-04** | Las versiones de los dos archivos de software, por el procedimiento de la seccion 4 |

Cerrar esas siete filas es, en la practica, el primer trabajo del banco.
