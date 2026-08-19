# A-04 y A-05 — Solicitudes de cuenta corporativa

**Estado: BORRADORES LISTOS PARA ENVIAR. No enviados.**
Preparados el 2026-08-19. Quien los envie rellena la fecha en `docs/POR-VERIFICAR.md`.

Tres solicitudes, una por canal. Van juntas porque **A-04 es la puerta de A-05, A-01 y A-06**: la
misma conversacion resuelve requisitos de cuenta, precio de distribuidor, certificacion por SKU y
buena parte del linaje de cadena de suministro.

## A quien

| Canal | Proveedor | Que surte | Por que este |
|---|---|---|---|
| Seguridad y baja tension | **ADI Global Distribution Canada** | Camaras premium (Axis, Hanwha), sensores, cableado, racks, Z-Wave | Es la ruta a las camaras del segmento sensible a linaje |
| Domotica | **Aartech Canada** | Inovelli, coordinadores Zigbee y Z-Wave, sensores | Unica ruta canadiense a Inovelli sin importacion directa. **Clave para A-08** |
| Electrico quebequense | **Franklin Empire** *(alternativas: Lumen, Guillevin)* | Sinope, Stelpro, interruptores, tomas, cable | Linea de mayor volumen en Quebec, soporte en frances, mostrador local |

Se empieza por uno de los tres electricos quebequenses, no por los tres a la vez: la respuesta del
primero dice que documentacion piden todos.

## Prerrequisito

**R-16, prueba de seguro.** Varias cuentas la exigen. Si no esta lista, la solicitud se envia igual y
se anota que el seguro esta en tramite: sirve para saber que mas piden y con que plazos.

## Datos a rellenar

| Campo | Valor |
|---|---|
| Razon social | _(rellenar)_ |
| Numero de empresa | _(rellenar)_ |
| Direccion de facturacion y de entrega | _(rellenar)_ |
| Persona de contacto y cargo | _(rellenar)_ |
| Correo y telefono | _(rellenar)_ |
| Poliza de responsabilidad civil | _(pendiente de R-16)_ |
| Licencia de contratista, si aplica | _(pendiente de R-03, R-04, R-06)_ |

## Texto de la solicitud

Adaptar el idioma: **frances** para Franklin Empire, Lumen y Guillevin; ingles para ADI y Aartech.

> Subject: Business account application — residential smart home integration, Ontario and Quebec
>
> Hello,
>
> We are opening a smart home integration business serving Ontario and Quebec, specialising in
> locally hosted systems for residential customers. We would like to open a business account with
> you and would appreciate your help with the following.
>
> **1. Account requirements.** What do you need from us to open an account: business number, proof
> of liability insurance, contractor licence, trade references, minimum order volume? Please include
> the current amounts and the expected timeline.
>
> **2. Pricing.** Once the account is open, we would like your current distributor price list for the
> categories below.
>
> **3. Certification documentation.** This is important to us and we ask for it up front: **for each
> device that is installed inside an electrical box or connected to line voltage, we need the
> datasheet showing the Canadian certification mark — cULus, cETL or CSA — for the specific
> stock-keeping unit you would ship us.** We are aware that manufacturers ship differently certified
> variants of the same model name for different markets, so we need the mark for the SKU, not for the
> model family. We verify the mark on the physical unit at receiving as well, but we would like the
> documentation before we specify anything.
>
> **4. Categories we buy.**
>
> - Switches, dimmers and controlled receptacles (Leviton Decora Smart, Inovelli, Sinopé)
> - Line-voltage thermostats (Sinopé, Stelpro) and 24 V thermostats
> - Fan-rated speed controls
> - PoE IP cameras, network switches with PoE+, access points, gateways
> - Sensors: door and window contacts, motion, water leak, temperature and humidity
> - Zigbee and Z-Wave coordinators
> - Cat6 and Cat6A cable, CMR and CMP rated, patch panels, wall-mount racks
> - Pure sine wave UPS with a data port
> - Surveillance-rated hard drives
>
> **5. Two specific questions.**
>
> - Do you carry the **Inovelli Blue Series 2-1**, and can you confirm its cETL listing and whether a
>   bypass module is required below a given load?
> - For the camera lines you carry, can you tell us the **manufacturing origin and supply chain
>   lineage**? A significant part of our target market is in the National Capital Region and this is a
>   purchase criterion for them, so we disclose it openly in our proposals.
>
> Thank you. We are happy to provide any documentation you need.
>
> _(signature, role, contact details)_

## Que se registra al recibir respuesta

En `datos-maestros/proveedores.yaml`, por proveedor:

- `requiere_cuenta_corporativa`, `requiere_licencia` — dejan de ser `null`
- `contacto_url` — cierra parte de B-03
- `cuenta_abierta` — a `true` solo cuando este operativa, no al solicitarla

En `datos-maestros/dispositivos/`, segun lo que llegue:

- `certificacion` y `fuente_url` por SKU — avanza **A-01**
- `precio_distribuidor_cad` — avanza **A-05**
- La respuesta sobre Inovelli avanza **A-08**; la de linaje de camaras, **A-06**

**Regla:** `verificado: true` solo con documento a la vista, no con una respuesta de mostrador. Una
confirmacion verbal se anota en `notas` y la fila sigue abierta.
