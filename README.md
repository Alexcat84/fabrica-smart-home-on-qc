# Fabrica de despliegues - Smart home local-first (Ontario y Quebec)

Repositorio de ingenieria de una integradora de smart homes **local-first** para Ontario y Quebec.
No es un almacen de configuraciones: es una **fabrica de despliegues**. Cada cliente se genera desde
plantillas versionadas mas un archivo de variables propio. Nada se construye a mano en casa del cliente.

> Alcance: iluminacion, tomas, ventiladores, termostatos y camaras.
> **Excluido sin excepcion:** incendio, gas, monoxido de carbono y todo sistema de seguridad de vida.
> El sistema no es una alarma monitoreada. Ver `docs/DECISIONES.md`, ADR-004.

## Dar de alta un cliente nuevo

```bash
# 1. Copiar la plantilla de variables y rellenarla con los datos del relevamiento
cp clientes/_plantilla-cliente.yaml clientes/APELLIDO-ciudad/cliente.yaml

# 2. Validar antes de comprar nada
python generador/validar.py clientes/APELLIDO-ciudad/cliente.yaml

# 3. Generar el paquete completo
python generador/generar.py clientes/APELLIDO-ciudad/cliente.yaml
```

El paso 3 escribe `salida/APELLIDO-ciudad/` con las configuraciones de todos los componentes, el
inventario de red, la lista de materiales con proveedores, los calculos justificados y los documentos
de cliente en ingles y frances. Despues: instalar fisicamente, afinar detalles e instalar la app.

## Estructura

| Directorio | Contenido |
|---|---|
| `catalogo/` | Dispositivos aprobados, excluidos, proveedores y componentes de software |
| `paquetes/` | Definicion de los paquetes S, M, L y XL |
| `plantillas/` | Plantillas Jinja del stack: Home Assistant, Frigate, Mosquitto, Zigbee2MQTT, red, respaldo |
| `clientes/` | Un archivo de variables por cliente. Nunca configuraciones completas |
| `generador/` | `validar.py` y `generar.py` |
| `herramientas/` | Calculadoras de almacenamiento, PoE y ancho de banda, con sus pruebas |
| `ansible/` | Roles y playbooks idempotentes para aprovisionar el controlador desde cero |
| `runbooks/` | Procedimientos operativos, en espanol |
| `plantillas-cliente/` | Documentos entregables al cliente, en ingles y frances |
| `docs/` | Arquitectura, seguridad, decisiones, nomenclatura, licencias y cola de verificacion |
| `salida/` | Paquetes generados. Artefacto derivado, no versionado |
| `referencia/` | Clones upstream solo para consulta. No versionado, nunca modificado |

## Primeros pasos en un clon nuevo

```bash
git config core.hooksPath .githooks    # activa la deteccion de secretos antes de cada commit
python -m unittest discover -s herramientas -p "test_*.py"
```

## Reglas inviolables

1. No se inventan numeros de parte, precios ni certificaciones.
2. Nada instalable en caja electrica sin marca canadiense visible (cULus, cETL o CSA).
3. Ningun componente puede requerir cuenta en la nube de un fabricante.
4. No hay fuego: nada toca seguridad de vida.
5. Ningun secreto en el repositorio.

Cada una esta razonada en `docs/DECISIONES.md` y verificada mecanicamente por `generador/validar.py`.
