# Esquemas

JSON Schema por tipo de registro. Existen para que **un campo mal escrito se rechace en lugar de
ignorarse**, que es el modo de fallo mas caro de un archivo YAML: `certificacon: CSA` no es un error
de sintaxis, es un campo que nadie lee y un dispositivo que parece certificado y no lo esta.

`additionalProperties: false` en todos. Anadir un campo nuevo obliga a declararlo aqui primero, que
es exactamente la friccion que se busca.

| Esquema | Aplica a |
|---|---|
| `dispositivo.schema.json` | Cada registro de `datos-maestros/dispositivos/*.yaml` |
| `proveedor.schema.json` | Cada registro de `datos-maestros/proveedores.yaml` |
| `excluido.schema.json` | Cada registro de `datos-maestros/excluidos.yaml` |
| `software.schema.json` | Cada registro de `software-cliente.yaml` y `software-empresa.yaml` |
| `paquete.schema.json` | Cada archivo de `comercial/paquetes/*.yaml` |

Los aplica `herramientas-empresa/validador/validar.py --catalogo`, y por tanto tambien
`verificar_todo.py` y el hook de pre-commit.
