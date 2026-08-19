# BANCO — Peticion de cotizacion de hardware

**Estado: BORRADOR LISTO PARA ENVIAR. No enviado.**
Preparado el 2026-08-19. Quien lo envie rellena la fecha en `docs/POR-VERIFICAR.md`.

Especificacion completa en [../BANCO.md](../BANCO.md). Esto es la lista de la compra.

## Por que se cotiza ahora y no despues

Ocho de los diez roles de `ansible/roles/` estan vacios a proposito. **No se escriben hasta que
exista el banco**, porque un rol sin ejecutar es una suposicion con sintaxis YAML. El banco es, por
tanto, el camino critico de todo el trabajo tecnico que queda.

Ademas cierra siete filas de `docs/POR-VERIFICAR.md` que no se pueden cerrar de ninguna otra forma:
A-08, A-02, M-02, M-04, M-11, M-13 y B-04.

## Lo que hay que cotizar

### Bloque 1 — Controlador

Dos equipos **identicos**: uno estable con la version desplegada en la flota, otro para probar la
siguiente. Sin el segundo, cada prueba de actualizacion deja el banco inservible hasta terminar.

| Cant. | Elemento | Especificacion | Nota |
|---|---|---|---|
| 2 | Micro escritorio empresarial reacondicionado | Dell OptiPlex Micro, Lenovo ThinkCentre Tiny o HP EliteDesk Mini. **Intel con graficos integrados, de la generacion mas antigua que se este comprando.** 16 GB RAM | Probar en un equipo moderno esconde los problemas de decodificacion e inferencia. Ver M-04 |
| 2 | NVMe de sistema | 250 a 500 GB | |
| 2 | Disco de vigilancia | WD Purple o Seagate SkyHawk, capacidad pequena admisible | Un SSD de consumo esconde el comportamiento de escritura continua |

### Bloque 2 — Red

| Cant. | Elemento | Especificacion | Por que |
|---|---|---|---|
| 1 | Pasarela con VLAN y cortafuegos con estado | Misma familia que se instala (UniFi u Omada), gestion autoalojada | La matriz direccional hay que aplicarla de verdad, no leerla |
| 1 | **Switch PoE+ gestionado, 8 puertos** | 802.1Q, presupuesto PoE conocido y publicado | Sin el **no son validables** los roles `red` ni `frigate`. Permite contrastar `calc_poe.py` contra consumo medido |
| 1 | Punto de acceso PoE | Multiples SSID mapeados a VLAN, WPA3 | Comprobar que la gestion no queda expuesta por radio |
| — | Cable Cat6 de parcheo | Varios, cortos | |

### Bloque 3 — Radio

| Cant. | Elemento | Especificacion | Por que |
|---|---|---|---|
| 1 | **Coordinador Zigbee por Ethernet o PoE** | Igual que en produccion, **no la variante USB** | Sin el **no es validable** el rol `zigbee2mqtt`. La ruta USB tiene otros modos de falla y probar en ella no dice nada de la de produccion |
| 1 | Interruptor Zigbee alimentado de red | Leviton Decora Smart o Sinope | Sin un dispositivo de red no se puede probar el orden de emparejamiento |
| 1 | **Inovelli Blue Series 2-1** | | **Cierra A-08**: operacion sin neutro, cETL y umbral de bypass |
| 1 | Termostato de tension de linea | Sinope o Stelpro | |
| 1 | Sensor Zigbee de bateria | Contacto o movimiento | Probar que se une a traves de una malla ya madura |

### Bloque 4 — Camaras

| Cant. | Elemento | Especificacion | Por que |
|---|---|---|---|
| **2** | **Camaras PoE de dos modelos DISTINTOS** | Una Reolink PoE y una de otra linea del catalogo (UniFi Protect, Axis o Hanwha) | **Dos modelos distintos es el requisito, no dos unidades.** Cierra M-02 (RTSP y ONVIF varian por modelo y firmware) y M-13 (bitrate y resolucion reales del sub-stream). Con una sola camara no se puede comparar nada |

### Bloque 5 — Energia y banco de pruebas

| Cant. | Elemento | Especificacion | Por que |
|---|---|---|---|
| 1 | UPS con puerto de datos | Onda senoidal pura | Network UPS Tools y el apagado ordenado hay que probarlos |
| 1 | Panel de pruebas con caja de interruptor **sin neutro** | Montaje de taller | Rama 2 del arbol de ADR-008. No se puede probar en una pared moderna |
| — | Lamparas LED | De los modelos que se supongan en propuestas | Fijar rangos de atenuacion y detectar parpadeo antes del salon de un cliente |

## Lo que no es hardware y hace falta igual

- **Enlace a internet con subida limitable**, o forma de estrangularla. Los tres escenarios de
  `calc_ancho_banda.py` hay que verlos fallar de verdad, no solo calcularlos.
- **Octeto `10.98.x.0/24` reservado** al banco en el registro de la empresa. El 99 es del cliente de
  demostracion; sin uno propio, la superposicion de soporte colisiona.

## A quien pedirla

La misma conversacion de A-04. Se puede enviar en el mismo correo o justo despues:

| Bloque | Canal |
|---|---|
| Controlador y discos | Reacondicionador canadiense (M-05) y retail de TI |
| Red | Revendedor de Ubiquiti u Omada, o retail de TI |
| Radio e Inovelli | **Aartech Canada** |
| Camaras | ADI Global Canada, y retail para la Reolink |
| UPS | Retail de TI |
| Panel de pruebas | Distribucion electrica quebequense |

## Que se registra al recibir la cotizacion

- Coste total del banco, para el plan financiero. Es inversion previa al primer proyecto pagado.
- Plazo de entrega de cada bloque. **El camino critico es lo que llegue mas tarde**, y probablemente
  sea el coordinador Zigbee por Ethernet o la segunda camara.
- Modelos y generaciones concretas disponibles, que alimentan M-04 y M-05.
