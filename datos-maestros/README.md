# datos-maestros/

La **unica fuente de verdad** sobre que es cada cosa. Todo lo demas referencia por identificador y no
redescribe.

| Archivo o directorio | Contenido |
|---|---|
| `dispositivos/` | Un archivo por categoria. 66 familias. Esquema comun en `dispositivos/_ESQUEMA.md` |
| `proveedores.yaml` | Canales de compra, con requisitos de cuenta |
| `excluidos.yaml` | Registro de exclusion, con motivo y regla violada |
| `software-cliente.yaml` | Lo que se entrega e instala en casa del cliente |
| `software-empresa.yaml` | Herramientas internas. Nunca se entregan |
| `esquemas/` | JSON Schema por tipo de registro |

## Por que hay dos archivos de software

Porque la obligacion de licencia se dispara con la **entrega**, no con el uso. Ansible es GPL-3.0 y
no genera ninguna obligacion, porque corre en nuestra estacion de trabajo y no se entrega. Mezclarlo
con Home Assistant en un solo archivo hacia esa distincion invisible justo donde importa. Ver el ADR
de la linea divisoria en `docs/DECISIONES.md`.

## Por que los esquemas

Para que un campo mal escrito se **rechace**, no se ignore. `certificacon: CSA` no es un error de
sintaxis YAML: es un campo que nadie lee y un dispositivo que parece certificado sin estarlo.

El primer dia que se aplicaron encontraron un fallo real que llevaba semanas en el repositorio:
`provincias: [ON, QC]` sin comillas, donde YAML interpreta `ON` como el booleano `true`. Ontario
llevaba tiempo siendo `True` en los datos maestros.
