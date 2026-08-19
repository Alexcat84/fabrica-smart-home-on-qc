# Convencion de nombres

Un tecnico que nunca ha visto una instalacion debe poder leerla sin abrir la documentacion. Esa es la
prueba a la que responde este documento. Si un nombre necesita explicacion, el nombre esta mal.

Se aplica a areas, dispositivos, entidades, automatizaciones, etiquetas de cable, puertos de switch y
nombres de camara. `herramientas-empresa/validador/validar.py` comprueba mecanicamente la parte verificable.

---

## 1. Terminos prohibidos (ADR-004)

**Regla absoluta.** Ninguna entidad, area, automatizacion, panel, notificacion o etiqueta de cable
puede contener, en ningun idioma, un termino que sugiera funcion de seguridad de vida.

| Prohibido | Por que | Que se usa en su lugar |
|---|---|---|
| `smoke`, `humo`, `fumee` | Sugiere deteccion de incendio | No aplica: fuera de alcance |
| `fire`, `fuego`, `incendie` | Idem | No aplica |
| `co`, `carbon_monoxide`, `monoxyde` | Sugiere deteccion de monoxido | No aplica |
| `gas`, `gaz` | Sugiere deteccion de gas | `calidad_aire`, `air_quality`, `qualite_air` |
| `alarm`, `alarma`, `alarme` | Sugiere sistema de alarma monitoreado | `aviso`, `alerta`, `alert`, `deterrent` |
| `panic`, `panico` | Sugiere alerta medica o de emergencia | No aplica |
| `emergency`, `emergencia`, `urgence` | Idem | No aplica |
| `life_safety`, `securite_vie` | Explicito | No aplica |
| `siren` como *alarma* | La sirena es disuasoria, no alarma | `disuasion`, `deterrent`, `dissuasion` |

Casos que aparecen de verdad y hay que nombrar bien:

- Un sensor de calidad de aire se llama `sensor.calidad_aire_sala`, **nunca** `sensor.gas_sala`. Su
  `friendly_name` en el panel del cliente dice explicitamente que no es un detector de gas.
- Un sensor de temperatura que avisa de congelacion se llama `binary_sensor.aviso_congelacion_sotano`,
  nunca `..._alarma_...`.
- La sirena se llama `switch.disuasion_sirena_interior`, nunca `switch.alarma_...`.
- La automatizacion que suena la sirena se llama `automation.disuasion_intrusion_planta_baja`.

`validar.py` rechaza el archivo de cliente si encuentra cualquiera de estos terminos en un nombre de
ubicacion, de dispositivo o de automatizacion. Es un error duro, no una advertencia.

---

## 2. Areas

Una area por espacio fisico real. Sin abreviaturas y sin numeros de habitacion inventados.

```
planta_baja_sala          rez_de_chaussee_salon
planta_baja_cocina        rez_de_chaussee_cuisine
planta_baja_entrada
planta_primera_dormitorio_principal
planta_primera_bano
sotano_taller
exterior_frente
exterior_patio
garaje
rack
```

Formato: `<nivel>_<espacio>` en minusculas y con guion bajo. El nivel va primero porque agrupa
naturalmente en cualquier lista ordenada, que es como el tecnico busca.

Los nombres de area son internos y en espanol. Los `friendly_name` que ve el cliente se generan en
ingles y frances desde el archivo de cliente.

---

## 3. Dispositivos

```
<categoria>_<area>_<discriminador>
```

- `interruptor_planta_baja_sala_principal`
- `interruptor_planta_baja_sala_lampara_pie`
- `termostato_planta_primera_dormitorio_principal`
- `camara_exterior_frente_entrada`
- `sensor_fuga_sotano_calentador`

El discriminador solo aparece cuando hay mas de un dispositivo de la misma categoria en la misma area.
No se numeran (`_1`, `_2`) salvo que el espacio fisico realmente no distinga: un numero no le dice
nada al tecnico que esta delante de la pared.

---

## 4. Entidades

Home Assistant construye `<dominio>.<objeto>`. El objeto sigue el nombre del dispositivo:

```
light.interruptor_planta_baja_sala_principal
climate.termostato_planta_primera_dormitorio_principal
binary_sensor.contacto_planta_baja_entrada_puerta
sensor.calidad_aire_planta_baja_sala
camera.camara_exterior_frente_entrada
switch.disuasion_sirena_interior_pasillo
```

Regla: **el `entity_id` no cambia nunca despues del comisionamiento.** Cambiarlo rompe automatizaciones,
paneles e historico. Si el cliente quiere otro nombre visible, se cambia el `friendly_name`, que es
precisamente para eso.

---

## 5. Automatizaciones

```
<dominio>_<intencion>_<ambito>
```

| Dominio | Uso |
|---|---|
| `iluminacion` | Encendido, apagado, escenas, ocupacion |
| `clima` | Consignas, retroceso, programacion |
| `disuasion` | Sirenas, avisos de intrusion al propietario |
| `energia` | Desplazamiento de carga, control de cargas altas |
| `red` | Estado de enlace, avisos de conectividad |
| `sistema` | Respaldo, actualizaciones, salud, soporte remoto |
| `agua` | Fuga y corte |

Ejemplos:

```
automation.iluminacion_ocupacion_planta_baja_entrada
automation.clima_retroceso_nocturno_planta_primera
automation.agua_corte_por_fuga_sotano
automation.sistema_soporte_remoto_apertura
automation.sistema_soporte_remoto_expiracion
```

---

## 6. Paquetes de configuracion por dominio

`producto-cliente/stack/homeassistant/packages/` tiene un archivo por dominio, con los mismos nombres que la
tabla anterior: `iluminacion.yaml`, `clima.yaml`, `seguridad.yaml`, `energia.yaml`, `red.yaml`,
`sistema.yaml`.

`seguridad.yaml` contiene disuasion, contactos, movimiento y presencia. El nombre del archivo es
interno; **ninguna entidad dentro de el puede llamarse `alarma`** (seccion 1).

---

## 7. Red, cable y puertos

| Elemento | Formato | Ejemplo |
|---|---|---|
| Etiqueta de cable | `<panel>-<puerto>` en ambos extremos | `PP1-07` |
| Puerto de switch | Descripcion = destino del cable | `PP1-07 camara_exterior_frente_entrada` |
| Nombre de host | `<categoria>-<discriminador>` | `cam-frente-entrada`, `ap-planta-primera` |
| VLAN | Nombre en ingles, como en la matriz de firewall | `Trusted`, `IoT`, `Camera`, `Controller`, `Management`, `Guest` |
| Reserva DHCP | Nombre de host igual que la etiqueta de cable cuando aplica | |

Los nombres de VLAN se mantienen en ingles a proposito: coinciden con la matriz de firewall del
capitulo 7.4.1 del plan de negocio y con la interfaz del equipo de red. Traducirlos crearia dos
vocabularios para la misma cosa.

Toda bajada se etiqueta en **ambos** extremos con el codigo que aparece en el plano as-built. Un cable
sin etiqueta es un defecto de instalacion, no un detalle pendiente.

---

## 8. Camaras

```
camara_<zona>_<vista>
```

`camara_exterior_frente_entrada`, `camara_exterior_patio_norte`, `camara_garaje_interior`.

El nombre describe **lo que la camara ve**, no donde esta atornillada. Cuando el cliente pide "el
video de la puerta de entrada", el tecnico encuentra la camara sin abrir el plano.

---

## 9. Idioma

| Artefacto | Idioma |
|---|---|
| `entity_id`, nombres de area, nombres de automatizacion, etiquetas de cable | Espanol interno, sin acentos ni enes |
| `friendly_name` y todo lo que ve el cliente | Ingles y frances, generados desde el archivo de cliente |
| Runbooks y comentarios de configuracion | Espanol |
| Nombres de VLAN | Ingles (seccion 7) |

Sin acentos ni `n` con virgulilla en identificadores: sobreviven mal en `entity_id`, en nombres de
host, en rutas de archivo y en interfaces de equipos de red. En el texto que ve el cliente, los
acentos son obligatorios y correctos.
