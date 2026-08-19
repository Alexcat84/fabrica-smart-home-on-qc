# Prompt de continuacion — sesion 2

Copia todo lo que sigue (desde la linea de guiones) y pegalo en Claude Code, en el directorio del
repositorio.

---

# ESTADO

Trabajas en `fabrica-smart-home-on-qc`, el repositorio de ingenieria de una integradora de smart
homes local-first para Ontario y Quebec. Las fases 0 a 4 estan completas y en `main`. Lee primero
`README.md`, `docs/DECISIONES.md` (las cinco reglas inviolables) y `docs/POR-VERIFICAR.md` (la cola
de trabajo real).

# PRIMER PASO, OBLIGATORIO

`git add -A && git commit` y `git push` de lo pendiente en la rama activa. Despues crea la rama de
esta sesion.

# COMPROBACION DE ARRANQUE

```bash
python herramientas/verificar_todo.py
```

Los diez pasos deben pasar antes de tocar nada. Si alguno falla, arreglar eso es el primer trabajo.

# LO QUE TOCA EN ESTA SESION

Elige con el usuario entre estos frentes. Estan en orden de valor:

## A. Vaciar la cola de urgencia ALTA (recomendado)

Siete filas de `docs/POR-VERIFICAR.md` bloquean el primer proyecto pagado. Ninguna se resuelve
escribiendo codigo: son llamadas, cuentas de distribucion y verificaciones fisicas. El trabajo del
repositorio es soportarlas:

- A-01: certificacion por SKU de los 22 dispositivos instalables en caja.
- A-02: ruta de control local de Lutron Caseta sin cuenta de fabricante. **Si no existe, cae ADR-003
  y hay que sustituir la solucion de referencia para cajas sin neutro**, que es el caso mas frecuente
  del parque antiguo. Es el riesgo tecnico mas serio del catalogo.
- A-03: modulo de dosel certificado para Canada.
- A-04 y A-05: requisitos de apertura de cuenta y precio real de distribuidor.
- A-06: linaje de cadena de suministro de camaras.
- A-07: limite de duracion de sirena del reglamento de ruido de Ottawa, Gatineau y Montreal.

A medida que se verifiquen: actualizar el YAML, poner `verificado: true`, rellenar `fuente_url`,
borrar la fila de la tabla y anotarla en el registro de verificaciones del final del documento.

## B. Completar los roles de ansible

`base/` y `soporte_remoto/` estan implementados. Los otros ocho (`docker`, `homeassistant`,
`frigate`, `mosquitto`, `zigbee2mqtt`, `red`, `backup`, `monitorizacion`) son esqueletos con
`tasks/main.yml` vacio a proposito: no se escribieron a ciegas porque no habia banco donde probarlos.

Se implementan contra el banco de la empresa, uno por uno, verificando idempotencia: ejecutar dos
veces seguidas no debe cambiar nada la segunda vez. El objetivo que hay que poder demostrar es el de
`runbooks/restaurar-controlador.md`: reconstruccion completa en menos de cuatro horas.

## C. Fijar versiones del stack

`catalogo/software.yaml` tiene los 27 componentes con `version_fijada: null`. Se fijan al
estandarizar el banco, no antes. Hasta entonces no hay despliegue reproducible de verdad (ADR-006).

## D. Segundo cliente real

Copiar `clientes/_plantilla-cliente.yaml`, rellenarlo con un relevamiento real y validarlo. Es la
prueba de que la fabrica sirve para algo mas que para el demo. **Ojo:** el validador rechaza a
proposito la verificacion de certificacion marcada `EJEMPLO-NO-REAL` en cualquier cliente que no
declare `es_ejemplo: true`. Eso es deliberado, no un fallo.

# REGLAS QUE NO CAMBIAN

1. No se inventan numeros de parte, precios ni certificaciones. `null` y fila en POR-VERIFICAR.
2. Nada instalable en caja electrica sin marca canadiense visible (cULus, cETL o CSA).
3. Ningun componente puede requerir cuenta en la nube de un fabricante.
4. No hay fuego: nada toca seguridad de vida.
5. Ningun secreto en el repositorio.

Ramas por fase, un commit por unidad logica, mensajes en espanol. `README` y runbooks en espanol; lo
que ve el cliente, en ingles y frances.

# AL CERRAR

Commitea y pushea todo. Entrega: (1) que quedo hecho, (2) que quedo abierto, (3)
`docs/POR-VERIFICAR.md` en orden de urgencia, y (4) el prompt de continuacion para la siguiente
sesion, empezando por commitear y pushear lo pendiente.
