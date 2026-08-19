# Politica de licencias de software libre

Esto es un asunto comercial y legal, no filosofico, y los integradores lo ignoran de forma rutinaria.

## La pregunta que lo decide todo

> **¿Queda instalado en el equipo que el cliente se lleva?**

Si la respuesta es **si**, eso es **distribucion** en el sentido legal de estas licencias, y la
obligacion se activa. Si es **no**, no hay obligacion, por copyleft que sea la licencia.

El disparador es la **entrega**, no el uso. Es ADR-010 en `docs/DECISIONES.md`, e implementado como
separacion fisica en los datos maestros:

| | `datos-maestros/software-cliente.yaml` | `datos-maestros/software-empresa.yaml` |
|---|---|---|
| Que es | Se instala en hardware del cliente | Corre en nuestra estacion de trabajo o en el banco |
| Es distribucion | **Si** | No |
| Obligacion | Segun licencia | **Ninguna, sea cual sea** |
| En el apendice del cliente | Si | **No** |
| Componentes | 26 | 6 |

**Ansible es GPL-3.0 y no genera ninguna obligacion.** Se ejecuta desde nuestra estacion de trabajo
contra el anfitrion del cliente por SSH, y no queda instalado en el equipo que se le vende. Lo mismo
con Git, GPL-2.0. Los dos estan en el lado de empresa con `obligacion_licencia: ninguna`, y es
correcto.

Este es el error que la separacion evita: cuando los 27 componentes vivian en un solo archivo,
Ansible aparecia con la misma obligacion que Zigbee2MQTT, como si las dos nos exigieran lo mismo.
Sobrestimar la obligacion lleva a publicar codigo que no hace falta publicar; subestimarla lleva a
entregar un binario modificado sin la fuente correspondiente, que si es un incumplimiento real.

---

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

`modificado_por_nosotros` esta en `false` en los 32 componentes. Esa columna vacia en el apendice del
cliente **es** la respuesta a cualquier pregunta sobre cumplimiento.

`referencia/` existe solo para consultar codigo upstream. Esta en `.gitignore`, nunca se commitea y
nunca se modifica. Todo lo nuestro vive en `producto-cliente/` como configuracion generada.

---

## Obligacion por familia de licencia, en el lado del cliente

Aplica **solo** a `software-cliente.yaml`. Para `software-empresa.yaml` la columna derecha seria
"ninguna" en todas las filas.

| Familia | Componentes entregados | Obligacion al entregar en hardware del cliente |
|---|---|---|
| Apache-2.0, MIT, BSD, EPL | Home Assistant OS y Core, Mosquitto, Z-Wave JS UI, Frigate, go2rtc, Traefik, NGINX, Authelia, Authentik, Uptime Kuma, Restic, Borg, rclone, CrowdSec, VictoriaMetrics | Conservar avisos de copyright y de licencia. **Entregar el apendice con cada instalacion.** |
| GPL-2.0 y GPL-3.0 | Zigbee2MQTT (GPL-3.0), ESPHome, WireGuard (GPL-2.0), Network UPS Tools (GPL-2.0) | Si **modificamos** el componente y lo entregamos, hay que ofrecer al destinatario la fuente correspondiente. Sin modificacion, basta el aviso. |
| AGPL-3.0 | Vaultwarden, Grafana | Igual que GPL, y ademas la obligacion se activa por **uso en red de una version modificada**, aunque no haya entrega de binarios. Politica: no se modifican. |

Casos concretos resueltos de antemano:

- **Nuestros YAML de ESPHome y nuestras automatizaciones de Home Assistant son obra nuestra.** Son
  configuracion, no obra derivada del codigo del proyecto. Se quedan en este repositorio privado.
- **Ansible es herramienta interna.** Ver arriba. Los roles de `herramientas-empresa/ansible/` son
  obra nuestra.
- **Los paneles de Grafana y de Home Assistant son configuracion**, igual que arriba.
- **Vaultwarden se entrega al cliente en el cierre del proyecto**, sin modificar. Aviso en el
  apendice y nada mas.

---

## Que se entrega al cliente

Todo paquete generado incluye un apendice de licencias, producido **solo** desde
`software-cliente.yaml` y filtrado por lo que ese cliente tiene desplegado. Por componente:

1. Nombre y version fijada.
2. Licencia.
3. URL del repositorio upstream.
4. **URL del parche publicado, si lo hubiera.** En condiciones normales esta columna esta vacia en
   toda la tabla, que es exactamente el objetivo.

Si algun componente tuviera `modificado_por_nosotros: true`, el generador anade una seccion aparte
que lo nombra y da la URL de la fuente correspondiente. Si la URL faltara, el apendice imprime
`PENDIENTE DE PUBLICAR`, que es visible y molesto a proposito.

`validar.py` **rechaza** un archivo de cliente que declare como desplegado un componente de
`software-empresa.yaml`. No es un descuido de catalogo: es afirmar que se entrega algo que no se
entrega.

---

## Disciplina de marca

Los nombres de los proyectos se usan de forma descriptiva y nunca de un modo que sugiera respaldo,
certificacion o asociacion comercial. La empresa vende **su propio servicio**, construido sobre
proyectos de software libre con nombre propio.

Esto convive con ADR-011, que decide entregar la interfaz **sobre** Home Assistant y su aplicacion
Companion: usar el producto y nombrarlo con precision no es lo mismo que insinuar una asociacion
comercial que no existe.

---

## Sin traspaso de garantia

Todas estas licencias renuncian a cualquier garantia. El contrato debe decirlo con claridad:

> La empresa garantiza su propia mano de obra de instalacion y su configuracion. No garantiza, y no
> puede garantizar, el software subyacente, que es software libre licenciado por terceros y
> distribuido sin garantia de ningun tipo.

Esta frase, o su equivalente en frances, aparece en la declaracion de alcance de todo cliente
(`producto-cliente/documentos/declaracion-de-alcance.*`).

---

## Si alguna vez hay que parchear

1. Se documenta el motivo como ADR en `docs/DECISIONES.md`: por que ningun mecanismo soportado sirve.
2. Se publica el parche en un repositorio publico de la empresa.
3. Se ponen `modificado_por_nosotros: true` y `url_parche_publicado` en el registro del componente.
4. El apendice del cliente incluye la URL automaticamente, en su propia seccion.
5. Se revisa en cada actualizacion upstream si el parche sigue siendo necesario. Un parche que nadie
   revisa se convierte en un fork de facto, que es justo lo que esta politica evita.
