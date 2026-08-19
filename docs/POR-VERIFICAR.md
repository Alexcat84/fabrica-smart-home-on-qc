# Cola de verificacion

Todo dato que este repositorio no conoce con certeza vive aqui hasta que alguien lo confirma contra la
fuente primaria. Es una cola de trabajo, no un apendice. La regla que la crea es ADR-001 en
`docs/DECISIONES.md`: no se inventan numeros de parte, precios ni afirmaciones de certificacion.

## Como se usa

1. Un campo `null` con `verificado: false` en `catalogo/` **debe** tener su fila aqui.
2. Cuando se verifica un dato: se actualiza el YAML, se pone `verificado: true`, se rellena `fuente_url`
   y se **borra** la fila de esta tabla, anotandola en el registro de verificaciones del final.
3. La verificacion de certificacion se hace sobre la marca impresa en la unidad fisica en recepcion,
   no sobre una pagina web. Los fabricantes envian variantes distintas del mismo nombre de modelo segun
   el mercado.

## Leyenda de urgencia

| Urgencia | Significado | Plazo |
|---|---|---|
| **ALTA** | Bloquea una cotizacion, una compra o una inspeccion. No se puede vender sin esto. | Antes del primer proyecto pagado |
| **MEDIA** | Bloquea el diseno detallado o el margen real, pero no la propuesta inicial. | Antes de abrir cuentas de distribucion |
| **BAJA** | Mejora la precision del catalogo. No bloquea nada. | Continuo |

## Pendientes

| # | Urgencia | Que hay que verificar | Donde vive el dato | Fuente a consultar | Bloquea |
|---|---|---|---|---|---|
| _(se puebla en la Fase 1)_ | | | | | |

## Registro de verificaciones completadas

| Fecha | Dato | Resultado | Quien | Fuente |
|---|---|---|---|---|
| _(vacio)_ | | | | |
