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
python generador/validar.py clientes/APELLIDO-ciudad/cliente.yaml

# 3. Generar el paquete completo
python generador/generar.py clientes/APELLIDO-ciudad/cliente.yaml

# 4. Aprovisionar el anfitrion
ansible-playbook -i ansible/inventario/APELLIDO-ciudad.yml \
    ansible/playbooks/aprovisionar-controlador.yml
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
python herramientas/verificar_todo.py
```

Ejecuta las 68 pruebas, valida el catalogo, genera el cliente de demostracion y comprueba las reglas
inviolables sobre el resultado.

## Estructura

| Directorio | Contenido |
|---|---|
| `catalogo/` | Dispositivos aprobados, excluidos, proveedores y componentes de software |
| `paquetes/` | Definicion de los paquetes S, M, L y XL |
| `plantillas/` | Plantillas Jinja del stack: Home Assistant, Frigate, Mosquitto, Zigbee2MQTT, red, respaldo |
| `clientes/` | Un archivo de variables por cliente. Nunca configuraciones completas |
| `generador/` | `validar.py` y `generar.py`, con sus pruebas de regresion |
| `herramientas/` | Calculadoras de almacenamiento, PoE y ancho de banda, y el detector de secretos |
| `ansible/` | Roles y playbooks idempotentes para aprovisionar el controlador desde cero |
| `runbooks/` | Procedimientos operativos, en espanol |
| `plantillas-cliente/` | Los cuatro documentos entregables, en ingles y frances |
| `docs/` | Arquitectura, seguridad, decisiones, nomenclatura, licencias y cola de verificacion |
| `salida/` | Paquetes generados. Artefacto derivado, **no versionado** |
| `referencia/` | Clones upstream solo para consulta. No versionado, nunca modificado |

## Primeros pasos en un clon nuevo

```bash
git config core.hooksPath .githooks    # activa la deteccion de secretos antes de cada commit
python herramientas/verificar_todo.py
```

El hook es la implementacion de ADR-005 y no depende de instalar nada: solo git y python.

## Reglas inviolables

1. **No se inventan** numeros de parte, precios ni certificaciones.
2. Nada instalable en caja electrica **sin marca canadiense visible** (cULus, cETL o CSA).
3. Ningun componente puede **requerir cuenta en la nube** de un fabricante.
4. **No hay fuego**: nada toca seguridad de vida.
5. **Ningun secreto** en el repositorio.

Cada una esta razonada en `docs/DECISIONES.md` y verificada mecanicamente por `generador/validar.py`.
Las pruebas de `generador/test_validar.py` comprueban que siguen teniendo dientes.

## Documentacion

| Documento | Para que |
|---|---|
| `docs/DECISIONES.md` | Por que el repositorio es como es. Empezar por aqui |
| `docs/ARQUITECTURA.md` | Que hace el sistema, que sale de la casa y como se dimensiona |
| `docs/SEGURIDAD.md` | Checklist de endurecimiento, acceso de soporte, segmentacion, incidentes |
| `docs/NOMENCLATURA.md` | Como se nombra todo, y que terminos estan prohibidos |
| `docs/LICENCIAS.md` | Politica de no forkear y que se entrega al cliente |
| `docs/POR-VERIFICAR.md` | **Cola de trabajo real**, ordenada por urgencia |
| `runbooks/` | Como se hace cada tarea recurrente |

## Estado

`docs/POR-VERIFICAR.md` esta poblada y ordenada por urgencia. Nada del catalogo esta verificado
todavia: es el estado correcto tras la primera sesion, no un defecto. Lo que bloquea el primer
proyecto pagado son las siete filas de urgencia ALTA, encabezadas por la certificacion por SKU y la
apertura de cuentas de distribucion.
