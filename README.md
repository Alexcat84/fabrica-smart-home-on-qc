# Fabrica de despliegues — Smart home local-first (Ontario y Quebec)

Repositorio de ingenieria de una integradora de smart homes **local-first**. No es un almacen de
configuraciones: es una **fabrica de despliegues**. Cada cliente se genera desde plantillas
versionadas mas un archivo de variables propio. Nada se construye a mano en casa del cliente.

> **Alcance:** iluminacion, tomas, ventiladores, termostatos y camaras.
> **Excluido sin excepcion:** incendio, gas, monoxido de carbono y todo sistema de seguridad de vida.
> El sistema no es una alarma monitoreada. Ver `docs/DECISIONES.md`, ADR-004.

---

## Dar de alta un cliente nuevo

```bash
# 1. Copiar la plantilla de variables y rellenarla con los datos del relevamiento
mkdir clientes/APELLIDO-ciudad
cp clientes/_plantilla-cliente.yaml clientes/APELLIDO-ciudad/cliente.yaml

# 2. Validar ANTES de comprar nada
python herramientas-empresa/validador/validar.py clientes/APELLIDO-ciudad/cliente.yaml

# 3. Generar el paquete completo
python herramientas-empresa/generador/generar.py clientes/APELLIDO-ciudad/cliente.yaml

# 4. Aprovisionar el anfitrion
ansible-playbook -i herramientas-empresa/ansible/inventario/APELLIDO-ciudad.yml \
    herramientas-empresa/ansible/playbooks/aprovisionar-controlador.yml
```

El paso 3 escribe `salida/APELLIDO-ciudad/` con las configuraciones de todos los componentes, el
inventario de red, la lista de materiales con proveedores, los calculos justificados y los cuatro
documentos de cliente en **ingles y frances**. Despues: instalar fisicamente, comisionar segun
`docs/SEGURIDAD.md`, afinar detalles e instalar la app en los moviles.

El paso 2 no es opcional. Rechaza el cliente si un dispositivo no esta en el catalogo, si algo que va
en caja electrica no tiene certificacion canadiense verificada, si el almacenamiento no alcanza la
retencion prometida, si el presupuesto PoE no tiene 40 % de holgura, si la subida no da para los
visores previstos, si el octeto de red colisiona con otro cliente, o si algun nombre sugiere funcion
de seguridad de vida.

## Probar el repositorio

```bash
python herramientas-empresa/verificar_todo.py
```

Ejecuta las 68 pruebas, valida el catalogo, genera el cliente de demostracion y comprueba las reglas
inviolables sobre el resultado.

## Estructura

| Directorio | Contenido |
|---|---|
| `datos-maestros/` | **Unica fuente de verdad**: dispositivos por categoria, proveedores, exclusiones, software, y JSON Schema por tipo de registro |
| `producto-cliente/` | Todo lo que acaba en casa del cliente: `stack/`, `marca/`, `interfaz/`, `app/`, `documentos/` |
| `herramientas-empresa/` | Lo que **nunca** se entrega: `generador/`, `validador/`, `calculadoras/`, `ansible/`, `runbooks/` |
| `comercial/` | Paquetes S/M/L/XL y listas de materiales |
| `gestion/` | Vacio a proposito. Su alcance futuro esta fijado en `gestion/README.md` |
| `clientes/` | Un archivo de variables por cliente. Nunca configuraciones completas |
| `docs/` | Arquitectura, seguridad, decisiones, nomenclatura, licencias, banco y las dos colas de verificacion |
| `salida/` | Paquetes generados. Artefacto derivado, **no versionado** |
| `referencia/` | Clones upstream solo para consulta. No versionado, nunca modificado |

La division no es organizativa: **`producto-cliente/` se entrega y `herramientas-empresa/` no**, y esa
frontera es la que determina que licencias generan obligacion de distribucion. Ver el ADR de la linea
divisoria en `docs/DECISIONES.md`.

## Primeros pasos en un clon nuevo

```bash
git config core.hooksPath .githooks    # activa la deteccion de secretos antes de cada commit
python herramientas-empresa/verificar_todo.py
```

El hook es la implementacion de ADR-005 y no depende de instalar nada: solo git y python.

## Reglas inviolables

1. **No se inventan** numeros de parte, precios ni certificaciones.
2. Nada instalable en caja electrica **sin marca canadiense visible** (cULus, cETL o CSA).
3. Ningun componente puede **requerir cuenta en la nube** de un fabricante.
4. **No hay fuego**: nada toca seguridad de vida.
5. **Ningun secreto** en el repositorio.

Cada una esta razonada en `docs/DECISIONES.md` y verificada mecanicamente por `herramientas-empresa/validador/validar.py`.
Las pruebas de `herramientas-empresa/validador/test_validar.py` comprueban que siguen teniendo dientes.

## Documentacion

| Documento | Para que |
|---|---|
| `docs/DECISIONES.md` | Por que el repositorio es como es. Empezar por aqui |
| `docs/ARQUITECTURA.md` | Que hace el sistema, que sale de la casa y como se dimensiona |
| `docs/SEGURIDAD.md` | Checklist de endurecimiento, acceso de soporte, segmentacion, incidentes |
| `docs/NOMENCLATURA.md` | Como se nombra todo, y que terminos estan prohibidos |
| `docs/LICENCIAS.md` | Politica de no forkear y que se entrega al cliente |
| `docs/POR-VERIFICAR.md` | **Cola de trabajo tecnica y comercial**, ordenada por lo que desbloquea |
| `docs/POR-VERIFICAR-REGULATORIO.md` | Consultas a reguladores, aseguradoras y aduanas. Documento controlado |
| `docs/BANCO.md` | El banco de la empresa: que hardware, que se prueba y como se fijan las versiones |
| `herramientas-empresa/runbooks/` | Como se hace cada tarea recurrente |

## Estado

Nada del catalogo esta verificado todavia: es el estado correcto, no un defecto.

Dos colas de trabajo, con ritmos distintos:

- **`docs/POR-VERIFICAR.md`** (tecnica y comercial) esta ordenada **por lo que desbloquea**. Empieza
  por abrir cuentas de distribucion (A-04, A-05), porque es el canal por el que se responden casi
  todas las demas filas de urgencia ALTA.
- **`docs/POR-VERIFICAR-REGULATORIO.md`** encabeza con **R-01**: si instalar camaras sin panel de
  intrusion exige licencia de agencia de seguridad privada en Quebec. **Bloquea toda venta en la
  provincia** y es la primera llamada del negocio.

Antes de escribir los ocho roles de ansible que faltan hay que montar el banco descrito en
`docs/BANCO.md`. Un rol sin banco es una suposicion con sintaxis YAML.
