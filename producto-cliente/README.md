# producto-cliente/

Todo lo que acaba **en casa del cliente**, y nada mas. La frontera importa por dos motivos:

1. **Licencias.** La obligacion de distribucion se dispara al entregar software en hardware del
   cliente. Lo que vive aqui se entrega; lo de `herramientas-empresa/` no. Ver el ADR de la linea
   divisoria en `docs/DECISIONES.md`.
2. **Migracion.** `marca/` e `interfaz/` estan separadas de `stack/` para que un cambio de capa de
   presentacion sea cambio de envase y no rehacer el producto.

| Directorio | Contenido |
|---|---|
| `stack/` | Configuracion de los componentes: Home Assistant, Frigate, Mosquitto, Zigbee2MQTT, red, respaldo |
| `marca/` | Tema, paleta, logo y textos de marca. Uno solo para toda la flota |
| `interfaz/` | Paneles, vistas e i18n en ingles y frances |
| `app/` | Flujo de alta, guia de instalacion y aprovisionamiento del movil |
| `documentos/` | As-built, acta de aceptacion, declaracion de alcance e informe de relevamiento, en EN y FR |
