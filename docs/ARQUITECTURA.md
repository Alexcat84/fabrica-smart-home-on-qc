# Arquitectura

## 1. Que es este repositorio

Una **fabrica de despliegues**. No un almacen de configuraciones de cliente.

```
  datos-maestros/ + comercial/paquetes/         clientes/<cliente>/cliente.yaml
  + producto-cliente/
        (lo que es igual en todas las casas)     (lo unico que es de esta casa)
                        \                       /
                         \                     /
                          v                   v
                        herramientas-empresa/validador/validar.py   -->  rechaza antes de comprar nada
                          |
                          v
                        herramientas-empresa/generador/generar.py
                          |
                          v
                        salida/<cliente>/
                          configuraciones + inventario de red + lista de materiales
                          + calculos justificados + documentos EN/FR
                          |
                          v
            herramientas-empresa/ansible/  -->  aprovisiona el anfitrion desde cero
```

Cuando llega un cliente nuevo el trabajo es: rellenar su archivo de variables, ejecutar el generador,
instalar fisicamente, afinar detalles e instalar la app. Todo lo demas ya existe aqui.

**Objetivo de recuperacion declarado y verificable:** reconstruccion completa de un controlador
destruido, desde plantilla mas respaldo, **en menos de cuatro horas**, sin conocimiento tribal. Si
una prueba de restauracion tarda mas, el defecto esta en la plantilla o en la documentacion, y se
corrige ahi.

---

## 2. Frontera de alcance

| Dominio | Dentro | Fuera |
|---|---|---|
| Iluminacion | Interruptores, atenuadores, reles, lamparas, escenas, horarios, control por ocupacion | Iluminacion de emergencia y de evacuacion |
| Tomas | Tomas controladas, modulos enchufables, medicion de energia | Toda toma que alimente equipo de seguridad de vida |
| Ventiladores | Ventiladores de techo sobre control con clasificacion para motor, extractores de bano, temporizadores y control por humedad | Enclavamientos de ventilacion exigidos por codigo, control de recuperador de calor donde el codigo lo imponga |
| Clima | Termostatos de tension de linea y de 24 V, programacion por zona, retroceso, consigna remota | Controles de seguridad de aparatos de combustion, controles internos de caldera y de horno |
| Camaras | Camaras IP, grabacion local, deteccion de objetos, retencion local, visionado remoto | Verificacion de video por central, despacho de vigilantes |
| Sensores y avisos | Movimiento, contactos, fuga de agua, temperatura, humedad, calidad de aire, sirenas locales, notificacion al propietario | **Incendio, humo, monoxido de carbono, gas, alerta medica, alarma de intrusion monitoreada** |
| Red | LAN segmentada, PoE, VLAN, politica de cortafuegos, acceso remoto cifrado | Provision del servicio de internet del cliente |

La columna derecha no es una lista de cosas que aun no hacemos. Es ADR-004, y es permanente.

---

## 3. Estrategia de protocolo

| Protocolo | Papel | Por que |
|---|---|---|
| **Zigbee** | Primario: interruptores, atenuadores, termostatos, sensores, enchufes | Maduro, local, en malla, catalogo amplio. Los dispositivos alimentados de red actuan como routers y refuerzan la malla. Se gestiona por una capa de traduccion abierta, no por un concentrador propietario |
| **Z-Wave** | Secundario, donde la cobertura Zigbee o la disponibilidad flaquean | Menor riesgo de interferencia al evitar los 2,4 GHz. Catalogo mas pequeno. Util para contactos de puerta a larga distancia en casas grandes |
| **Matter y Thread** | Selectivo, mirando adelante | Buen modelo de control local, pero el ecosistema aun se consolida: se adopta dispositivo por dispositivo, no como compromiso de plataforma |
| **Wi-Fi** | Uso restringido | Aceptable para un numero reducido de modulos de rele en un segmento aislado dedicado. **Nunca para sensores de bateria** |
| **PoE** | Camaras, coordinadores, puntos de acceso, paneles tactiles | Un solo cable para datos y energia, respaldo centralizado, sin fuente local que falle |
| **Cableado de baja tension** | Contactos y sirenas donde sea practico | Maxima fiabilidad, sin baterias y sin radio. Preferido siempre que la pared este abierta |

**Regla de diseno:** una red Zigbee por propiedad, un coordinador, colocado centralmente y lejos del
rack. No se mezclan concentradores competidores. Cada ecosistema de radio adicional multiplica la
carga de soporte sin anadir capacidad.

---

## 4. Stack de software

```
                          +---------------------------+
   Telefono del cliente   |  Tunel WireGuard cifrado  |   Sin puertos abiertos
   (dentro o fuera)  <--->|  (claves del cliente)     |   en el router
                          +------------+--------------+
                                       |
                          +------------v--------------+
                          |  Proxy inverso (TLS)      |  Traefik o NGINX
                          +------------+--------------+
                                       |
   +-----------------+   +-------------v-------------+   +----------------------+
   | Zigbee2MQTT     |-->|                           |<--| Frigate + go2rtc     |
   | Z-Wave JS UI    |   |    Home Assistant Core    |   | (grabacion, deteccion|
   | ESPHome         |-->|                           |<--|  sobre iGPU Intel)   |
   +--------+--------+   +-------------+-------------+   +----------+-----------+
            |                          |                            |
            v                          v                            v
      +-----------+          +------------------+          +------------------+
      | Mosquitto |          | InfluxDB/Victoria|          | Discos vigilancia|
      | (auth     |          | + Grafana        |          | (WD Purple /     |
      |  obligat.)|          | Uptime Kuma      |          |  SkyHawk)        |
      +-----------+          +------------------+          +------------------+
            |
            v
   +--------------------+   +------------------+   +---------------------------+
   | Vaultwarden        |   | Restic o Borg    |   | Network UPS Tools         |
   | (baul del cliente) |   | + rclone         |   | (apagado ordenado)        |
   +--------------------+   +------------------+   +---------------------------+

   Ansible: herramienta INTERNA de la empresa. Aprovisiona todo lo anterior. No se entrega.
```

El detalle por componente, con licencia y obligacion practica, esta en `datos-maestros/software-cliente.yaml`.
La politica de licencias esta en `docs/LICENCIAS.md`. Resumen: **no forkeamos**.

---

## 5. Flujo de datos, y que sale de la casa

| Flujo | Sale de la propiedad | Notas |
|---|---|---|
| Video de camara al grabador | **No** | Segmento aislado, el grabador abre la conexion |
| Video del grabador al telefono del cliente | **No, en el sentido util**: viaja cifrado por el tunel entre el telefono y el servidor del propio cliente | Sin servidor de medios de terceros |
| Estado de dispositivos | **No** | Bus MQTT local |
| Historico de energia y ambiente | **No** | Base de series temporales local |
| Respaldo de configuracion | Solo si el cliente elige destino externo, **a su propia cuenta** | La empresa no aloja respaldos |
| **Notificacion push al movil** | **Si** | Unica excepcion arquitectonica. Contenido reducido a categoria y hora. Divulgada por escrito. Alternativa solo local disponible. Ver `docs/SEGURIDAD.md`, seccion 3.2 |
| Telemetria al fabricante | **No** | Ningun componente puede requerir cuenta de nube (ADR-003) |
| Acceso de la empresa | Solo durante una sesion que el cliente abre y que expira sola | Ver `docs/SEGURIDAD.md`, seccion 4 |

---

## 6. Segmentacion fisica y logica

Una sola red fisica. Hasta seis VLAN con separacion aplicada por cortafuegos direccional y con
estado. El segundo octeto se asigna por cliente desde el registro de la empresa, para que dos sitios
nunca colisionen cuando un tecnico esta conectado a ambos por la superposicion de soporte.

**Cuantas VLAN por nivel** (ADR-009):

| Paquete | VLAN | Presentes | Notas |
|---|---|---|---|
| S | 4 | Trusted, IoT, Camera, Controller | Management plegada en **Trusted**; sin Guest |
| M | 5 | + Guest | Management plegada en **Trusted** |
| L | 6 | + Management | Primer nivel con VLAN de gestion separada |
| XL | 6 o mas | Las seis | Separacion adicional por inquilino donde aplique |

Plegar Management **no relaja la politica**: las reglas que la nombran se aplican igualmente sobre
las interfaces de gestion, que en S y M viven dentro del segmento Trusted.

Se pliega en Trusted y **no en Controller** a proposito: el anfitrion del controlador contiene las
camaras y su grabacion, es el objetivo de mayor valor de la instalacion, y no debe tener alcance
administrativo sobre la pasarela ni los switches. **Controller nunca alcanza Management**, en ningun
nivel, plegada o separada.

```
   10.<octeto>.10.0/24   Trusted      familia
   10.<octeto>.20.0/24   IoT          reles, termostatos, enchufes, paneles
   10.<octeto>.30.0/24   Camera       camaras (sin salida, no originan conexiones)
   10.<octeto>.40.0/24   Controller   Home Assistant + grabador
   10.<octeto>.50.0/24   Management   pasarela, switches, puntos de acceso
   10.<octeto>.60.0/24   Guest        visitas, aisladas
```

La matriz completa esta en `producto-cliente/stack/red/firewall.yaml.j2` y explicada en `docs/SEGURIDAD.md`.

---

## 7. Dimensionado: tres calculos que se publican en cada propuesta

Los competidores citan periodos de retencion sin hacer el calculo. Nosotros lo adjuntamos.

| Calculo | Formula | Herramienta |
|---|---|---|
| Almacenamiento | `TB = (Mbps / 8) x 86400 x camaras x dias / 1e6` | `herramientas-empresa/calculadoras/calc_almacenamiento.py` |
| Presupuesto PoE | Suma del peor caso, con infrarrojo nocturno y calefactor, mas **40 % de holgura** | `herramientas-empresa/calculadoras/calc_poe.py` |
| Ancho de banda de subida | Dos escenarios: (1) sub-stream x visores + margen; (2) lo anterior mas el salto de una camara a stream principal | `herramientas-empresa/calculadoras/calc_ancho_banda.py` |

Regla practica de referencia: una camara a 8 Mbps consume unos 86 GB al dia.

`herramientas-empresa/validador/validar.py` rechaza el archivo de cliente si cualquiera de los tres no cuadra. Un
presupuesto PoE ajustado produce caidas intermitentes de camara de noche, y son extremadamente
dificiles de diagnosticar despues porque solo aparecen con frio y oscuridad.

---

## 8. Que se decide por cliente y que no

| Vive en el archivo de cliente | Vive en `producto-cliente/` |
|---|---|
| Identidad, provincia, idioma, paquete | Estructura de configuracion de todos los componentes |
| Segundo octeto de red | Plan de direccionamiento y matriz de cortafuegos |
| Inventario de dispositivos con ubicacion y circuito | Convencion de nombres |
| Camaras con campo de vision, bitrate, zonas y mascaras | Politica de retencion hibrida y ruta de inferencia |
| Retencion deseada | Formulas de dimensionado |
| Miembros del hogar y plataforma movil | Interruptor de soporte remoto y su temporizador |
| Preferencia de notificaciones | Contenido minimo de la notificacion |
| Plano de control autoalojado o comercial | Arquitectura del tunel |
| Canal Zigbee elegido tras el relevamiento | Reglas de construccion de la malla |

Comportamiento especifico del cliente vive en el archivo de variables y en definiciones de
automatizacion. **Nunca en ediciones manuales sin documentar.**
