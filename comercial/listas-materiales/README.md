# comercial/listas-materiales/

La lista de materiales de cada cliente **se genera**, no se escribe: sale de
`herramientas-empresa/generador/generar.py` a `salida/<cliente>/lista-de-materiales.md`, agrupada por
categoria y con los proveedores tomados de `datos-maestros/proveedores.yaml`.

Este directorio existe para lo que **no** es por cliente:

| Contenido previsto | Estado |
|---|---|
| Listas de materiales tipo por paquete, para cotizar sin relevamiento previo | Pendiente de A-05: sin precio de distribuidor real, una lista tipo es una lista de deseos |
| Plantillas de pedido por proveedor | Pendiente de A-04 |
| Kits recurrentes, por ejemplo el kit de rack o el kit de una camara exterior | Pendiente del banco |

**Ninguna de las tres se escribe todavia.** Las tres dependen de datos que ADR-001 prohibe inventar.
