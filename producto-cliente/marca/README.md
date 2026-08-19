# producto-cliente/marca/

Capa de marca, **separada y parametrizada** (ADR-011).

| Archivo | Contenido |
|---|---|
| `marca.yaml` | Identidad, paleta, tipografia, logo, modo kiosco, accesibilidad |
| `tema.yaml.j2` | Tema de Home Assistant, generado desde `marca.yaml` |

## Por que esta separada

Para que una migracion futura sea **cambio de envase y no rehacer el producto**. Ninguna plantilla de
`../stack/` contiene un color, una tipografia ni un texto de marca: los toma de aqui.

Si algun dia se cruza uno de los disparadores de ADR-011 -mas de 150 instalaciones, contrato que
exija marca propia, o un cambio aguas arriba que rompa el uso profesional-, lo que hay que reescribir
es esta capa y `../interfaz/`, no la logica ni los datos.

## Una sola para toda la flota

Lo especifico de un cliente es **la distribucion de zonas y la nomenclatura**, nunca el tema. Un tema
por cliente son quince temas que mantener a los quince clientes, y una correccion visual que hay que
aplicar quince veces.

`validar.py` rechaza un archivo de cliente que defina `tema`, `paleta` o `marca`.

## Por que casi todo esta en null

Porque no hay decision de diseno todavia, y ADR-001 aplica igual a un color que a un numero de parte:
un valor inventado ahora es un valor que hay que cambiar en dos sitios despues. Los unicos con valor
son los que no son estetica sino umbral: escala tipografica minima, contraste minimo y tiempo de
vuelta a inicio del modo kiosco.
