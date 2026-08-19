# producto-cliente/app/

La aplicacion es la **Companion de Home Assistant**. No se desarrolla aplicacion propia: ADR-011, con
sus tres motivos y sus tres disparadores para reabrir la decision.

Este directorio documenta lo que si es nuestro: **como se entrega la experiencia**.

| Documento | Para que |
|---|---|
| `flujo-de-alta.md` | Alta de un miembro del hogar, de principio a fin. Guion de cara al cliente |
| `guia-instalacion.md` | Que se instala en el telefono y en que orden |
| `aprovisionamiento.md` | Que queda configurado en el dispositivo movil al terminar |

## Los dos limites que se declaran en el diseno

No al final, ni cuando el cliente pregunte. **En la fase de diseno, por escrito** (ADR-011):

1. **El modelo de permisos por usuario es de grano grueso.** Sirve para separar a los miembros de un
   hogar. No es apto como barrera dura en alquiler o multiinquilino: ahi la separacion tiene que ser
   de red y de sistema, no de interfaz.
2. **Ver varias camaras de alta resolucion a la vez en la app es peor que en un visor NVR dedicado.**
   Se explica junto al calculo de ancho de banda, porque la causa es la misma.
