# Politica de licencias de software libre

Esto es un asunto comercial y legal, no filosofico, y los integradores lo ignoran de forma rutinaria.
Entregar software instalado en hardware que se vende a un cliente **es distribucion** en el sentido
legal de estas licencias. El momento de resolverlo es ahora, no cuando alguien pregunte.

## La regla que evita el problema entero

> **No forkeamos.**
>
> Configuramos y extendemos por los mecanismos soportados por cada proyecto: archivos de
> configuracion, plantillas, complementos, integraciones y automatizaciones. No parcheamos codigo
> upstream.
>
> Si un parche resulta genuinamente inevitable, se publica en un repositorio publico y se referencia
> ese repositorio en la documentacion del cliente. Eso convierte una carga de cumplimiento en una
> respuesta de dos lineas.

`referencia/` existe solo para consultar codigo upstream. Esta en `.gitignore`, nunca se commitea y
nunca se modifica. Todo lo nuestro vive en `producto-cliente/stack/` como configuracion generada.

## Que obligacion tiene cada familia de licencia

| Familia | Componentes en nuestro stack | Obligacion al entregar en hardware del cliente |
|---|---|---|
| Apache-2.0, MIT, BSD, EPL | Home Assistant OS y Core, Mosquitto, Z-Wave JS UI, Frigate, go2rtc, Traefik, NGINX, Authelia, Authentik, Uptime Kuma, Restic, Borg, rclone, CrowdSec, VictoriaMetrics | Conservar avisos de copyright y de licencia. **Entregar el apendice de licencias con cada instalacion.** |
| GPL-2.0 y GPL-3.0 | Zigbee2MQTT (GPL-3.0), ESPHome, WireGuard (GPL-2.0), Network UPS Tools (GPL-2.0), Ansible (GPL-3.0) | Si **modificamos** el componente y lo entregamos, hay que ofrecer al destinatario la fuente correspondiente. Sin modificacion, basta el aviso. |
| AGPL-3.0 | Vaultwarden, Grafana | Igual que GPL, y ademas la obligacion se activa por **uso en red** de una version modificada, aunque no haya entrega de binarios. Politica: no se modifican. |

Casos concretos que conviene tener resueltos de antemano:

- **Nuestros YAML de ESPHome y nuestras automatizaciones de Home Assistant son obra nuestra.** Son
  configuracion, no obra derivada del codigo del proyecto. Se quedan en este repositorio privado.
- **Ansible es herramienta interna.** Se ejecuta desde la estacion de trabajo de la empresa contra el
  anfitrion del cliente; no se entrega al cliente. No hay distribucion, no hay obligacion.
- **Los paneles de Grafana son configuracion**, igual que arriba.
- **Vaultwarden se entrega al cliente en el cierre del proyecto**, sin modificar. Aviso de licencia en
  el apendice y nada mas.

## Que se entrega al cliente

Todo paquete generado incluye un apendice de licencias con, por cada componente desplegado:

1. Nombre y version fijada.
2. Licencia, con su texto o un enlace estable a el.
3. URL del repositorio upstream.
4. Si esta modificado, la URL del repositorio publico con el parche. En condiciones normales esta
   columna esta vacia en toda la tabla, que es exactamente el objetivo.

El apendice se genera desde `datos-maestros/software-cliente.yaml` filtrando los componentes que corresponden al
paquete del cliente. No se mantiene a mano.

## Disciplina de marca

Los nombres de los proyectos se usan de forma descriptiva y nunca de un modo que sugiera respaldo,
certificacion o asociacion comercial. La empresa vende **su propio servicio**, construido sobre
proyectos de software libre con nombre propio. No somos socios de Home Assistant, de Frigate ni de
ninguno de los demas, y no lo insinuamos en material de venta.

## Sin traspaso de garantia

Todas estas licencias renuncian a cualquier garantia. El contrato debe decirlo con claridad:

> La empresa garantiza su propia mano de obra de instalacion y su configuracion. No garantiza, y no
> puede garantizar, el software subyacente, que es software libre licenciado por terceros y
> distribuido sin garantia de ningun tipo.

Esta frase, o su equivalente en frances, aparece en la declaracion de alcance de todo cliente
(`producto-cliente/documentos/declaracion-de-alcance.*`).

## Si alguna vez hay que parchear

1. Se documenta el motivo como ADR en `docs/DECISIONES.md`: por que ningun mecanismo soportado sirve.
2. Se publica el parche en un repositorio publico de la empresa.
3. Se referencia esa URL en `datos-maestros/software-cliente.yaml`, en el campo `notas` del componente.
4. El apendice de licencias del cliente incluye la URL automaticamente.
5. Se revisa en cada actualizacion upstream si el parche sigue siendo necesario. Un parche que nadie
   revisa se convierte en un fork de facto, que es justo lo que esta politica evita.
