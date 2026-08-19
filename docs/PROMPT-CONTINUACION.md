# Prompt de continuacion — sesion 4

Copia todo lo que sigue (desde la linea de guiones) y pegalo en Claude Code, en el directorio del
repositorio.

---

# ESTADO

Trabajas en `fabrica-smart-home-on-qc`, el repositorio de ingenieria de una integradora de smart
homes local-first para Ontario y Quebec. Las fases 0 a 6 estan completas y en `main`.

Lee primero, en este orden:

1. `README.md`
2. `docs/DECISIONES.md` — doce ADR. Las cinco primeras son las reglas inviolables
3. `docs/POR-VERIFICAR-REGULATORIO.md` — **empieza por R-01**
4. `docs/POR-VERIFICAR.md` — cola tecnica, y las tres acciones preparadas del 2026-08-19
5. `docs/BANCO.md` — requisito previo a escribir roles de ansible

# PRIMER PASO, OBLIGATORIO

`git add -A && git commit` y `git push` de lo pendiente en la rama activa. Despues crea la rama de
esta sesion.

# COMPROBACION DE ARRANQUE

```bash
python herramientas-empresa/verificar_todo.py
```

Los once pasos deben pasar antes de tocar nada.

# LO PRIMERO: TRES ACCIONES QUE ESPERAN FUERA DEL REPOSITORIO

Los textos estan redactados en `docs/consultas/`. **Ninguno esta enviado.** Enviarlos no es trabajo
del repositorio, pero es lo que desbloquea casi todo lo demas.

| Accion | Borrador | Desbloquea |
|---|---|---|
| **R-01** al Bureau de la securite privee | `docs/consultas/R-01-bureau-securite-privee.md` | **Toda venta en Quebec** |
| **A-04 / A-05**, cuentas de distribucion | `docs/consultas/A-04-A-05-cuentas-de-distribucion.md` | A-01, A-06 y parte de A-02 |
| **Cotizacion del banco** | `docs/consultas/BANCO-cotizacion-hardware.md` | Los ocho roles de ansible, y ocho filas de la cola tecnica |

Al enviarlos, rellenar la fecha de envio en su fila. Al recibir respuesta, actualizarla y aplicar la
consecuencia. **Una llamada telefonica no cierra una fila regulatoria**: se pide confirmacion por
escrito y se archiva.

# LO QUE TOCA EN ESTA SESION

## A. La cola regulatoria

R-01 bloquea toda venta en Quebec. Detras van R-06 (RBQ) y R-09 (comerciante itinerante), que
tambien deciden si se puede firmar un contrato, y R-16 (seguro), prerrequisito de varias cuentas de
distribucion.

Falta abrir **R-18**, trabajo en altura y seguridad en construccion (item 23 del cap. 14). Quedo
anotada sin fila para no simular cobertura; abrela cuando haya personal contratado.

## B. Montar el banco, y solo entonces escribir los roles

`docs/BANCO.md` tiene la tabla de estado por rol con tres columnas. Tres roles salen **No** y dos
**Parcial**: sin coordinador Zigbee por Ethernet, dos camaras PoE de modelos distintos y switch PoE+
gestionado, `zigbee2mqtt`, `frigate` y `red` **no son validables**.

Criterio de aceptacion de cada rol: `changed=0` en la segunda pasada, medido. Y el **ensayo de
reversion** de la seccion 3.2.1, que es criterio distinto del de restauracion: menos de 30 minutos y
**cero datos perdidos**.

El banco cierra ademas ocho filas de la cola tecnica: A-08, A-02, M-02, M-04, M-11, M-13, M-14 y
B-04.

## C. Cerrar M-14, que arrastra los minimos publicados

Los minimos de subida de los cuatro paquetes se recalcularon con un **perfil de camara calculado**,
no con camaras medidas. M-14 los convierte en datos reales. El de M subio de 10 a 15 y los de L y XL
bajaron; los cuatro se revisan cuando haya medicion en banco.

## D. Segundo cliente real

Copiar `clientes/_plantilla-cliente.yaml` y validarlo. El validador rechaza a proposito, y no son
fallos:

- Verificacion de certificacion `EJEMPLO-NO-REAL` en un cliente sin `es_ejemplo: true`.
- Una camara sin `bitrate_substream_mbps` o sin `streams_soportados` medidos.
- Un componente de `software-empresa.yaml` declarado como desplegado.
- Un cliente que defina tema, paleta o marca propios.

## E. Cuando `gestion/` tenga sentido

Sigue vacio a proposito. Su entrada principal ya existe:
`salida/<cliente>/dispositivos-instalados.yaml`, que el generador emite vacio para rellenar en obra.
El primer contenido de `gestion/` deberia salir del **primer proyecto pagado**, no de una sesion de
diseno.

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
- **ADR-009 y su enmienda**: Management es VLAN separada de L en adelante; en S y M se pliega en
  **Trusted**, no en Controller. **Controller nunca alcanza Management**, en ningun nivel.
- **ADR-003, enmienda**: Lutron Caseta es excepcion documentada, no ruta por defecto.
- **ADR-010**: la obligacion de licencia se dispara con la **entrega**, no con el uso. Ansible es
  GPL-3.0 y no genera ninguna obligacion.
- **ADR-011**: la interfaz se entrega sobre Home Assistant. Un solo tema para toda la flota.
- **ADR-012**: tres roles de flujo de camara, tres escenarios de ancho de banda, y **prohibido
  transcodificar en el servidor**.
- Los identificadores de las colas **no se renumeran** al reordenarlas.

# NOTAS PRACTICAS DEL ENTORNO

- El heredoc de Bash **colapsa la barra invertida seguida de n a un salto de linea real**. Para
  codigo Python con escapes, usar la herramienta de edicion, no un heredoc.
- YAML 1.1: `ON`, `OFF`, `YES` y `NO` sin comillas son **booleanos**, y las fechas sin comillas son
  objetos `date`. Las dos cosas ya causaron fallos reales y las dos las detectaron los esquemas, no
  una revision humana.

# AL CERRAR

Commitea y pushea todo. Entrega: (1) que quedo hecho, (2) que quedo abierto, (3) el estado de las dos
colas, y (4) el prompt de continuacion para la siguiente sesion, empezando por commitear y pushear lo
pendiente.
