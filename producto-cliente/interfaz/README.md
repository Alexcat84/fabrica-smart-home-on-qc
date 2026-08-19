# producto-cliente/interfaz/

Paneles, vistas e internacionalizacion. Capa separada de `../stack/` por el mismo motivo que
`../marca/`: para que una migracion futura sea cambio de envase y no rehacer el producto (ADR-011).

| Directorio | Contenido |
|---|---|
| `dashboards/` | Biblioteca de paneles. **Una sola para toda la flota** |
| `i18n/` | Textos que ve el cliente, en ingles y frances |

## Que es del producto y que es del cliente

| Del producto, igual en toda la flota | Del cliente |
|---|---|
| Tema, paleta, tipografia | Nombres de zona y su traduccion |
| Estructura de las vistas | Que dispositivos hay en cada zona |
| Textos de interfaz | Preferencia de notificaciones |
| Semantica de color de estado | Que miembros del hogar ven que |

`validar.py` rechaza un archivo de cliente que cruce esa linea definiendo tema, paleta o marca.

## Reglas de los textos

Los dos archivos de `i18n/` estan sujetos a ADR-004: **ningun texto puede sugerir funcion de
seguridad de vida**. Nada de "alarm", "emergency", "fire", "smoke", "gas", "alarme", "urgence",
"incendie". La lista completa esta en `docs/NOMENCLATURA.md`, seccion 1, y `verificar_todo.py` la
comprueba sobre el paquete generado.

Los mensajes que salen por notificacion push llevan el **minimo**: categoria y hora. Sin imagen, sin
nombre de camara y sin detalle de ubicacion. El motivo esta en `docs/SEGURIDAD.md`, seccion 3.2.
