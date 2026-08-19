# gestion/

**Vacio a proposito.** Este README fija su alcance futuro para que nadie lo llene con lo primero que
haga falta.

## Que va a vivir aqui

La capa de **gestion del negocio**, que es lo unico que este repositorio todavia no modela:

| Area | Que abarca | De donde saca los datos |
|---|---|---|
| Ordenes de trabajo | Visita, sesion remota, tecnico, motivo, acciones. Es la evidencia que exige la normativa de privacidad | `clientes/`, y el registro de soporte del propio cliente |
| Parque instalado | Que unidad fisica esta en que casa, con su numero de serie y su garantia | El registro DISPOSITIVO INSTALADO, ver commit siguiente |
| Inventario | Existencias, minimos, plazos de reposicion | `datos-maestros/dispositivos/` |
| Compras | Pedidos a proveedor, recepcion y verificacion de marca | `datos-maestros/proveedores.yaml` |
| Planes de cuidado | Altas, renovaciones, no renovaciones, congelacion de version | `clientes/` |
| Programacion | Ventanas de actualizacion, pruebas de restauracion anuales | `herramientas-empresa/runbooks/` |

## Que NO va a duplicar

Esta es la parte que importa. Lo siguiente **se consume desde donde ya vive** y no se copia aqui:

- **El catalogo.** `datos-maestros/dispositivos/` es la unica fuente de verdad de que es cada
  producto. Gestion referencia por `sku_interno`, nunca redescribe el dispositivo.
- **Los proveedores.** `datos-maestros/proveedores.yaml`. Gestion referencia por `id`.
- **Las variables de cliente.** `clientes/<cliente>/cliente.yaml`. Gestion no guarda una segunda
  copia de la direccion, del paquete ni del inventario de un cliente.
- **Los precios.** Viven en el catalogo, con su fecha y su procedencia. Una lista de precios paralela
  en gestion diverge en semanas.
- **La configuracion desplegada.** Se regenera desde plantillas. Gestion no guarda configuraciones.

La regla, en una linea: **gestion guarda hechos que ocurren en el tiempo -esta unidad se instalo, este
pedido llego, esta sesion de soporte paso-, no descripciones de cosas.** Las descripciones estan en
`datos-maestros/`.

## Por que esta vacio

Porque modelar la gestion antes de tener un solo cliente real produce un modelo de datos que hay que
tirar. El primer contenido de este directorio deberia salir del **primer proyecto pagado**, no de una
sesion de diseno.

Lo unico que se adelanta es el **registro de dispositivo instalado**
(`datos-maestros/esquemas/dispositivo-instalado.schema.json`), porque es la union entre inventario,
parque instalado y garantia, y el generador ya lo emite vacio en cada paquete
(`salida/<cliente>/dispositivos-instalados.yaml`) para que se rellene en obra.

Ese registro guarda **hechos**: que unidad fisica, con que numero de serie, en que casa, desde que
dia y hasta cuando en garantia. Referencia el producto por `sku_interno` y no lo redescribe. Cuando
`gestion/` exista de verdad, ese archivo sera su entrada principal, y por eso su esquema se escribio
antes que el resto.
