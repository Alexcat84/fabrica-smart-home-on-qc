# Runbooks

Procedimientos operativos, en espanol, uno por tarea recurrente. Se escriben para que **otra persona**
los ejecute: si un paso necesita que preguntes, el runbook esta incompleto y se corrige.

| Runbook | Cuando |
|---|---|
| [emparejar-dispositivo.md](emparejar-dispositivo.md) | Anadir un dispositivo Zigbee o Z-Wave |
| [sustituir-camara.md](sustituir-camara.md) | Una camara falla o se cambia de modelo |
| [restaurar-controlador.md](restaurar-controlador.md) | El controlador muere. Objetivo: menos de cuatro horas |
| [incorporar-miembro-hogar.md](incorporar-miembro-hogar.md) | Alta de una persona del hogar |
| [aplicar-actualizacion.md](aplicar-actualizacion.md) | Actualizacion deliberada, con su reversion |
| [atender-sesion-soporte.md](atender-sesion-soporte.md) | El cliente abre una sesion de soporte |
| [congelar-version-cliente.md](congelar-version-cliente.md) | Un cliente no renueva el plan de cuidado |
| [responder-incidente-seguridad.md](responder-incidente-seguridad.md) | Incidente de seguridad |

## Reglas comunes a todos

1. **Ninguna sesion en un sistema de cliente sin que el cliente la abra.** No hay excepcion tecnica
   posible: no existe credencial permanente de la empresa en ningun sistema.
2. **Toda visita y toda sesion remota se registra en la orden de trabajo**, con tecnico, motivo y
   cambios. Es buena practica y es la base probatoria si alguna vez hay una queja de privacidad.
3. **Nada se edita a mano en casa del cliente.** Se corrige la plantilla o el archivo de variables y
   se regenera (ADR-006). Un cambio manual desaparece en la siguiente regeneracion y, peor, deja de
   estar en control de versiones.
4. **Instantanea antes de tocar nada** que pueda romperse.
5. **Nada de este repositorio toca seguridad de vida** (ADR-004). Si un procedimiento parece
   necesitarlo, el procedimiento esta mal.
