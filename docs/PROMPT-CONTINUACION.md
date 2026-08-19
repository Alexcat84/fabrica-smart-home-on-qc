# Prompt de continuacion — sesion 3

Copia todo lo que sigue (desde la linea de guiones) y pegalo en Claude Code, en el directorio del
repositorio.

---

# ESTADO

Trabajas en `fabrica-smart-home-on-qc`, el repositorio de ingenieria de una integradora de smart
homes local-first para Ontario y Quebec. Las fases 0 a 5 estan completas y en `main`.

Lee primero, en este orden:

1. `README.md`
2. `docs/DECISIONES.md` — nueve ADR. Las cinco primeras son las reglas inviolables
3. `docs/POR-VERIFICAR-REGULATORIO.md` — **empieza por R-01**
4. `docs/POR-VERIFICAR.md` — cola tecnica, ordenada por lo que desbloquea
5. `docs/BANCO.md` — requisito previo a escribir roles de ansible

# PRIMER PASO, OBLIGATORIO

`git add -A && git commit` y `git push` de lo pendiente en la rama activa. Despues crea la rama de
esta sesion.

# COMPROBACION DE ARRANQUE

```bash
python herramientas-empresa/verificar_todo.py
```

Los diez pasos deben pasar antes de tocar nada. Si alguno falla, arreglar eso es el primer trabajo.

# LO QUE TOCA EN ESTA SESION

Los frentes estan en orden de riesgo, no de comodidad. Elige con el usuario.

## A. R-01, y el resto de la cola regulatoria

**R-01 bloquea toda venta en Quebec**: si instalar camaras IP y sensores locales sin panel de
intrusion y sin monitoreo exige licencia de agencia de seguridad privada. Es la primera llamada del
negocio y ninguna cantidad de codigo compensa equivocarse ahi.

Detras van R-06 (RBQ) y R-09 (comerciante itinerante), que tambien afectan a si se puede firmar un
contrato en Quebec, y R-16 (seguro), que es prerrequisito para abrir varias cuentas de distribucion.

El trabajo del repositorio aqui es de registro, no de codigo: actualizar estado, fecha y respuesta
escrita en `docs/POR-VERIFICAR-REGULATORIO.md`, y aplicar la consecuencia donde toque. **No cierres
una fila con una llamada telefonica**: se pide confirmacion por correo y se archiva.

Falta abrir **R-18** (trabajo en altura y seguridad en construccion, item 23 del cap. 14), que quedo
anotada pero sin fila para no simular cobertura. Abrela cuando haya personal contratado.

## B. Montar el banco, y solo entonces escribir los roles

`docs/BANCO.md` especifica hardware minimo, que se prueba y como se fijan las 27 versiones.

Ocho roles de `herramientas-empresa/ansible/roles/` siguen siendo esqueletos a proposito: `docker`, `homeassistant`,
`frigate`, `mosquitto`, `zigbee2mqtt`, `red`, `backup`, `monitorizacion`. `base` y `soporte_remoto`
si estan implementados.

**No los escribas sin banco.** Un rol sin ejecutar es una suposicion con sintaxis YAML. El criterio
de aceptacion de cada uno es `changed=0` en la segunda pasada, medido, y va a la tabla de la seccion
3.1 de `docs/BANCO.md`.

El banco cierra ademas siete filas de la cola tecnica de una sola vez: A-08, A-02, M-02, M-04, M-11,
M-13 y B-04.

## C. Abrir el canal de distribucion

A-04 y A-05 encabezan la cola tecnica **porque son la via por la que se responden A-01, A-06 y parte
de A-02**. Una conversacion con el distribuidor resuelve precio, disponibilidad, certificacion por
SKU y buena parte del linaje. Requiere R-16 (prueba de seguro) resuelto antes.

## D. Cerrar el arbol de ADR-008

A-08 (Inovelli Blue 2-1 sin neutro, cETL, y a partir de que carga exige bypass) es la fila que
decide si la rama 2 del arbol se cubre **sin puente propietario**. Si sale a favor, la excepcion de
Lutron Caseta deja de ser necesaria y el catalogo vuelve a un solo ecosistema de radio.

Si A-02 (a) sale en contra, Caseta pasa al registro de exclusion y hay que reescribir la rama 2.

## E. Segundo cliente real

Copiar `clientes/_plantilla-cliente.yaml`, rellenarlo con un relevamiento real y validarlo.

Dos cosas que el validador rechaza a proposito y no son fallos:

- La verificacion de certificacion marcada `EJEMPLO-NO-REAL` en cualquier cliente que no declare
  `es_ejemplo: true`.
- Una camara sin bitrate de sub-stream medido, ni en catalogo ni en el archivo de cliente.

# REGLAS QUE NO CAMBIAN

1. No se inventan numeros de parte, precios ni certificaciones. `null` y fila en la cola.
2. Nada instalable en caja electrica sin marca canadiense visible (cULus, cETL o CSA).
3. Ningun componente puede requerir cuenta en la nube de un fabricante.
4. No hay fuego: nada toca seguridad de vida.
5. Ningun secreto en el repositorio.

Ramas por fase, un commit por unidad logica, mensajes en espanol. `README` y runbooks en espanol; lo
que ve el cliente, en ingles y frances.

# COSAS QUE YA SE DECIDIERON, NO LAS REABRAS SIN MOTIVO

- **ADR-008**: la iluminacion sin neutro es un arbol de tres ramas, no una solucion de referencia.
- **ADR-009**: Management es VLAN separada de L en adelante. 4 / 5 / 6 / 6.
- **ADR-003, enmienda**: Lutron Caseta es excepcion documentada, no ruta por defecto.
- El ancho de banda se evalua en **dos escenarios** y los dos tienen que caber.
- Los identificadores de las colas **no se renumeran** al reordenarlas.

# AL CERRAR

Commitea y pushea todo. Entrega: (1) que quedo hecho, (2) que quedo abierto, (3) el estado de las dos
colas en orden de urgencia, y (4) el prompt de continuacion para la siguiente sesion, empezando por
commitear y pushear lo pendiente.
