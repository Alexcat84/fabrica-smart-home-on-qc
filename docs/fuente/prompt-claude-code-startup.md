# Prompt de arranque para Claude Code

Copia todo lo que sigue (desde la línea de guiones) y pégalo en Claude Code, en un directorio vacío.

---

# MISIÓN

Vas a crear desde cero el repositorio de ingeniería de una empresa de integración de smart homes local-first en Ontario y Quebec, Canadá. El repositorio es una **fábrica de despliegues**: cada cliente se genera desde plantillas versionadas más un archivo de variables propio. Nada se construye a mano en casa del cliente.

El objetivo operativo final: cuando llegue un cliente nuevo, el trabajo se reduce a (1) rellenar su archivo de variables, (2) ejecutar el generador, (3) instalar físicamente, (4) afinar detalles y (5) instalar la app en sus celulares. Todo lo demás ya existe en el repo.

## PROCESO DE TRABAJO, OBLIGATORIO EN CADA RONDA

1. **Antes de cualquier trabajo nuevo: `git add -A && git commit` y `git push` de lo pendiente en la rama activa.** Si el repo no existe todavía, este primer paso es `git init`, crear `.gitignore` y hacer el commit raíz.
2. Trabaja en ramas por fase: `fase-0-esqueleto`, `fase-1-catalogo`, `fase-2-stack`, `fase-3-generador`, `fase-4-runbooks`.
3. Un commit por unidad lógica de trabajo, con mensaje descriptivo en español.
4. Al terminar cada fase, resume qué quedó hecho, qué quedó abierto, y entrega el prompt de continuación para la siguiente sesión.

## REGLAS INVIOLABLES

- **No inventes números de parte, precios, ni afirmaciones de certificación.** Cada entrada del catálogo lleva los campos `certificacion`, `fuente_url` y `verificado: false`. Si no conoces el dato con certeza, escribe `null` y añade la fila a `docs/POR-VERIFICAR.md`. Un dato inventado en este repo se convierte más tarde en una inspección eléctrica rechazada.
- **Ningún dispositivo entra al catálogo como instalable en caja eléctrica si no tiene marca canadiense visible** (cULus, cETL o CSA). Los dispositivos con marcado europeo solamente van al registro de exclusión, con el motivo.
- **Ningún componente del stack puede requerir cuenta en la nube de un fabricante para funcionar.** Si un componente la requiere, va al registro de exclusión.
- **No hay fuego.** Nada en este repositorio toca detección de incendio, gas, monóxido de carbono, ni ningún sistema de seguridad de vida. Si una plantilla, automatización o etiqueta sugiere función de seguridad de vida, es un defecto y hay que corregirlo.
- **Nunca guardes secretos en el repo.** Contraseñas, claves y tokens van cifrados con `ansible-vault` o quedan como marcadores de posición. Añade un hook de pre-commit que detecte secretos.
- Los `README` y los runbooks se escriben en español. Los artefactos que ve el cliente se generan en inglés y francés.

---

# FASE 0. ESQUELETO

Crea esta estructura:

```
.
├── README.md
├── .gitignore
├── .pre-commit-config.yaml
├── catalogo/
│   ├── dispositivos.yaml
│   ├── excluidos.yaml
│   ├── proveedores.yaml
│   └── software.yaml
├── paquetes/
│   ├── S-essential.yaml
│   ├── M-standard.yaml
│   ├── L-premium.yaml
│   └── XL-estate.yaml
├── plantillas/
│   ├── homeassistant/
│   ├── frigate/
│   ├── mosquitto/
│   ├── zigbee2mqtt/
│   ├── red/
│   └── backup/
├── clientes/
│   ├── _plantilla-cliente.yaml
│   └── EJEMPLO-demo/
├── generador/
│   ├── generar.py
│   └── validar.py
├── ansible/
│   ├── inventario/
│   ├── roles/
│   └── playbooks/
├── herramientas/
│   ├── calc_almacenamiento.py
│   ├── calc_poe.py
│   └── calc_ancho_banda.py
├── runbooks/
├── plantillas-cliente/
│   ├── informe-relevamiento.md
│   ├── documento-as-built.md
│   ├── acta-de-aceptacion.md
│   └── declaracion-de-alcance.md
└── docs/
    ├── ARQUITECTURA.md
    ├── SEGURIDAD.md
    ├── POR-VERIFICAR.md
    └── DECISIONES.md
```

`docs/DECISIONES.md` es un registro de decisiones de arquitectura: una entrada por decisión, con fecha, contexto, opciones consideradas y motivo. Empieza registrando las cinco reglas inviolables de arriba.

---

# FASE 1. CATÁLOGO E INVENTARIO

## 1.1 `catalogo/dispositivos.yaml`

Esquema por dispositivo:

```yaml
- id: sinope-th1123zb
  categoria: termostato          # iluminacion | interruptor | rele | toma | ventilador |
                                 # termostato | sensor | camara | sirena | red | computo |
                                 # almacenamiento | energia | coordinador | cableado
  fabricante: Sinopé Technologies
  pais_fabricante: Canadá (Quebec)
  modelo: null                   # null si no lo verificaste
  protocolo: zigbee              # zigbee | zwave | wifi | matter | poe | cableado | ninguno
  tension: linea                 # linea | baja | bateria | poe
  instalable_en_caja: true
  certificacion: null            # cULus | cETL | CSA | null
  ised: null
  control_local_sin_nube: true
  disponibilidad_canada: distribuidor_electrico
  proveedores: [franklin-empire, lumen, guillevin]
  precio_lista_cad: null
  precio_distribuidor_cad: null
  paquetes: [S, M, L, XL]
  notas: "Termostato de voltaje de línea para plinthes eléctricas."
  fuente_url: null
  verificado: false
```

Puebla el catálogo con al menos estas categorías y familias, **sin inventar modelos ni precios**:

| Categoría | Familias a incluir |
|---|---|
| Iluminación | Lutron Caséta (sin neutro), Leviton Decora Smart, Inovelli Blue, Sinopé, lámparas Philips Hue / Sengled / IKEA |
| Relés y micromódulos | Shelly SKU norteamericano únicamente, módulos Inovelli, relés DIN certificados |
| Tomas | Toma inteligente Leviton, plug Sinopé, controladores de carga Sinopé |
| Ventiladores | Controles con clasificación para motor de ventilador (Lutron, Leviton, Inovelli), extractores de baño |
| Termostatos | Sinopé y Stelpro (voltaje de línea, Quebec), Ecobee y Honeywell T6 Z-Wave (24 V), interfaz local para mini-splits vía ESPHome |
| Sensores | Fuga de agua Sinopé más válvula de corte, contactos puerta/ventana, movimiento PIR, presencia mmWave, temperatura y humedad, calidad de aire |
| Sirenas | Sirena interior Zigbee, sirena y estrobo exterior con clasificación de intemperie |
| Cámaras | Ubiquiti UniFi Protect, Reolink PoE, Axis, Hanwha |
| Cómputo | Dell OptiPlex Micro, Lenovo ThinkCentre Tiny, HP EliteDesk Mini reacondicionados |
| Almacenamiento | WD Purple, Seagate SkyHawk, NVMe de sistema, NAS Synology |
| Red | Gateway y switches PoE+ UniFi u Omada, puntos de acceso, patch panels, Cat6 y Cat6A con clasificación CMR y CMP |
| Energía | UPS onda senoidal pura CyberPower y APC, con puerto de datos |
| Coordinadores | Coordinador Zigbee (preferente por Ethernet o PoE), stick Z-Wave |

## 1.2 `catalogo/excluidos.yaml`

Empieza con estas entradas, cada una con su motivo:

- Sonoff ZBMINIL2, módulos de relé Aqara, cualquier relé con marcado CE únicamente: sin certificación canadiense confirmada para instalación fija.
- Cualquier dispositivo que exija cuenta de fabricante en la nube para operar.
- Cámaras exteriores de cuerpo plástico de gama consumidor: fallo en clima frío, sin PoE, RTSP débil.
- Cámaras con linaje de cadena de suministro restringido o poco claro.
- Atenuadores de iluminación aplicados a motores de ventilador: riesgo de incendio.
- SSD de consumo para grabación continua de video: agotamiento de escritura.
- SKU europeos de marcas por lo demás aprobadas.

## 1.3 `catalogo/proveedores.yaml`

Un registro por proveedor con `id`, `nombre`, `tipo` (distribucion_seguridad, distribucion_electrica, fabricante_directo, retail_ti, reacondicionador), `provincias`, `requiere_cuenta_corporativa`, `requiere_licencia`, `categorias_que_surte`, `contacto_url: null`, `cuenta_abierta: false`.

Incluye al menos: ADI Global Canada, Aartech Canada, Nedco, Westburne, Guillevin, Franklin Empire, Lumen, Sinopé, Stelpro, canal de distribuidores Lutron, revendedores canadienses de Ubiquiti, Canada Computers, Memory Express, Newegg.ca, y una entrada genérica para reacondicionadores canadienses de equipo empresarial.

## 1.4 `catalogo/software.yaml`

Un registro por componente con `id`, `nombre`, `licencia`, `repo_url`, `version_fijada`, `rol`, `obligacion_licencia` (aviso, fuente_si_modificado, ninguna), `sustituible_por`, `paquetes`.

Componentes: Home Assistant OS y Core, Mosquitto, Zigbee2MQTT, Z-Wave JS UI, Frigate, go2rtc, ESPHome, WireGuard y el plano de control de la malla, Traefik o NGINX, Authelia o Authentik, Vaultwarden, InfluxDB o VictoriaMetrics, Grafana, Uptime Kuma, Restic o Borg, rclone, Network UPS Tools, CrowdSec, Ansible.

Marca claramente los componentes GPL y AGPL y anota la obligación: si los modificamos y los entregamos en hardware del cliente, eso es distribución y hay que ofrecer la fuente correspondiente. Genera `docs/LICENCIAS.md` explicando la política: **no forkeamos**, configuramos y extendemos por mecanismos soportados; si un parche es inevitable, se publica en repositorio público y se referencia en la documentación del cliente.

---

# FASE 2. STACK Y PLANTILLAS

Clona en `referencia/` (añadido a `.gitignore`, nunca commiteado) los repositorios upstream que necesites consultar, y **no los modifiques**. Todo lo nuestro vive en `plantillas/` como configuración generada.

Construye:

- `plantillas/homeassistant/`: `configuration.yaml` con Jinja, paquetes por dominio (iluminación, clima, seguridad, energía, red, sistema), convención de nombres de entidades y áreas documentada en `docs/NOMENCLATURA.md`, dashboards base, y el **interruptor de soporte remoto**: un `input_boolean` con temporizador de 2 horas, revocación al reinicio, registro local legible y notificación al cliente al abrir y al cerrar la sesión.
- `plantillas/frigate/`: configuración con detección por iGPU Intel (OpenVINO) como ruta por defecto, acelerador discreto como opción, sub-stream para detección y stream principal para grabación, retención híbrida (continua corta más eventos larga), y zonas y máscaras por cámara como variables.
- `plantillas/mosquitto/` y `plantillas/zigbee2mqtt/`: autenticación obligatoria, sin acceso anónimo, canal Zigbee como variable.
- `plantillas/red/`: definición declarativa de las seis VLAN (Trusted, IoT, Camera, Controller, Management, Guest) con la matriz de firewall direccional y con estado, el segundo octeto asignado por cliente, y un servidor de hora local dentro del segmento de cámaras.
- `plantillas/backup/`: Restic o Borg cifrado, copia local secundaria, destino externo opcional controlado por el cliente, y **prueba de restauración** como tarea programada verificable.
- `docs/SEGURIDAD.md`: la lista de endurecimiento completa como checklist ejecutable, incluyendo el escaneo externo de puertos al poner en servicio.

---

# FASE 3. GENERADOR

- `clientes/_plantilla-cliente.yaml`: todas las variables de un cliente (identidad, provincia, idioma, paquete, octeto de red, inventario de dispositivos con ubicación y circuito, cámaras con campo de visión y bitrate, retención deseada, miembros del hogar y sus plataformas móviles, preferencia de notificaciones, opción de plano de control autoalojado o comercial).
- `generador/validar.py`: rechaza el archivo de cliente si algún dispositivo no está en el catálogo, si un dispositivo marcado `instalable_en_caja` no tiene certificación, si el cálculo de almacenamiento no alcanza la retención pedida, si el presupuesto PoE no tiene 40 % de holgura, o si el ancho de banda de subida es insuficiente para los visores concurrentes previstos.
- `generador/generar.py`: produce el paquete completo del cliente en `salida/<cliente>/`: configuraciones de todos los componentes, inventario de red, lista de materiales con proveedores, cálculos justificados, y los documentos de cliente en inglés y francés a partir de `plantillas-cliente/`.
- `herramientas/`: implementa las tres calculadoras con las fórmulas siguientes y sus pruebas unitarias.
  - Almacenamiento: `TB = (Mbps / 8) * 86400 * camaras * dias / 1e6`.
  - PoE: suma del consumo en peor caso, incluyendo infrarrojo nocturno y calefactor, más 40 % de holgura.
  - Ancho de banda: bitrate del sub-stream por visores concurrentes, más margen para el tráfico del hogar.
- `ansible/`: roles idempotentes para aprovisionar el host del controlador desde cero, con versiones fijadas y actualizaciones automáticas deshabilitadas. Objetivo declarado: **reconstrucción completa desde plantilla más respaldo en menos de cuatro horas.**

---

# FASE 4. RUNBOOKS Y ENTREGABLES

`runbooks/` en español, uno por tarea recurrente: emparejar un dispositivo, sustituir una cámara, restaurar un controlador, incorporar a un miembro del hogar, aplicar una actualización con su reversión, atender una sesión de soporte, congelar la versión de un cliente que no renueva, y responder a un incidente de seguridad.

`plantillas-cliente/` en inglés y francés:
- Informe de relevamiento con la lista de verificación completa del sitio.
- Documento as-built con inventario de dispositivos, registro eléctrico, diagrama y direccionamiento de red, plan de cámaras con campos de visión, catálogo de automatizaciones en lenguaje llano, procedimiento de credenciales, procedimiento de respaldo y restauración, política de actualizaciones, y una **sección de continuidad** que explique exactamente cómo entregar el sistema a otro proveedor.
- Acta de aceptación con el protocolo de pruebas: desconectar el controlador y operar las luces desde la pared, desconectar internet, cortar la energía del rack, escaneo externo de puertos, acceso remoto desde red celular, aislamiento del segmento de cámaras, interruptor de soporte con su expiración, respaldo y restauración, y detección por cámara.
- Declaración de alcance con las exclusiones de seguridad de vida y la aclaración de que el sistema no es una alarma monitoreada.

# ENTREGABLE DE ARRANQUE

Al terminar, `EJEMPLO-demo` debe generar un paquete completo y validado de un cliente de paquete M, con cero errores de validación, y `README.md` debe explicar en menos de una página cómo se da de alta un cliente nuevo desde cero.

# AL CERRAR LA SESIÓN

Commitea y pushea todo. Luego entrega: (1) qué quedó hecho, (2) qué quedó abierto, (3) la lista de `docs/POR-VERIFICAR.md` en orden de urgencia, y (4) el prompt de continuación para la siguiente sesión, empezando por commitear y pushear lo pendiente.
