# Responder a un incidente de seguridad

Este runbook se lee **antes** de que haga falta. En el momento del incidente nadie lee documentacion
nueva.

## 1. Detectar

Un incidente entra por una de tres puertas:

- Alerta del monitoreo local (`Uptime Kuma`, registro del controlador, CrowdSec).
- Aviso del cliente.
- Divulgacion de vulnerabilidad upstream que afecta a un componente que tenemos desplegado.

La tercera es la mas frecuente y la que mas se descuida: hay que **vigilar activamente** los avisos
de los proyectos de `datos-maestros/software-cliente.yaml`.

## 2. Contener

El diseno de segmentacion convierte la contencion en un cambio de cortafuegos, no en una
reconstruccion. Aisla el segmento afectado o deshabilita el servicio afectado.

| Si el compromiso esta en... | Contencion inmediata |
|---|---|
| Una camara | Ya esta aislada: no origina conexiones. Deshabilitar su puerto de switch |
| Un dispositivo IoT | Deshabilitar su puerto o su acceso inalambrico; el segmento ya no alcanza Trusted |
| El controlador | Cortar su salida a internet y el tunel; el sistema local sigue funcionando |
| La pasarela o un switch | Aislar Management; acceso solo por consola fisica |

Anotar la hora exacta de cada accion. La cronologia es lo primero que se pregunta despues.

## 3. Evaluar

Determinar si se accedio a informacion personal.

Aqui se nota la decision de diseno: **la empresa no conserva video de cliente, ni transmisiones en
directo, ni grabaciones, ni telemetria continua**. La mayoria de incidentes afectan a
*disponibilidad*, no a *confidencialidad*, lo que reduce materialmente la carga de notificacion.

Preguntas a responder por escrito:

- [ ] Que sistema, que componente y que version.
- [ ] Ventana temporal de la exposicion.
- [ ] Que datos eran alcanzables desde ese punto.
- [ ] Hay evidencia de acceso efectivo, o solo de exposicion.
- [ ] Que credenciales pudieron quedar comprometidas.

## 4. Notificar

- **Al cliente, sin demora**, cuando haya informacion personal implicada. Con lo que se sabe y lo que
  todavia no se sabe, sin adornar.
- **Al regulador**, cuando se alcance el umbral legal.
- **Quebec exige registro de incidentes de confidencialidad con independencia de la gravedad.**
  Confirmar los umbrales y requisitos vigentes: es una de las filas de `docs/POR-VERIFICAR.md`.

## 5. Remediar y registrar

1. Parchear o sustituir el componente.
2. **Rotar todas las credenciales alcanzables** desde el punto comprometido. Todas, no las que
   parezcan afectadas.
3. Verificar que la via de entrada esta cerrada, con escaneo externo incluido.
4. Anotar el incidente en el registro, con cronologia y acciones.

## 6. Revisar la flota

**Este es el paso que la mayoria de integradores no da, y es la razon de que este repositorio exista.**

- [ ] Evaluar si la misma exposicion existe en el resto de instalaciones.
- [ ] Aplicar la correccion **en la plantilla**, no cliente por cliente.
- [ ] Regenerar y desplegar en todas las instalaciones afectadas.
- [ ] Si el incidente revela un fallo de diseno, escribir un ADR nuevo en `docs/DECISIONES.md`.

Una correccion aplicada a mano en un cliente es una correccion que los otros catorce no tienen.
