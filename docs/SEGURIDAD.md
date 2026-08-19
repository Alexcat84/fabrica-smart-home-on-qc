# Seguridad

El cliente compra la promesa de que sus datos no salen de su casa. Esa promesa vale exactamente lo
que valga la postura de seguridad del equipo que dejamos instalado. Un sistema local mal asegurado es
**peor** que un servicio en la nube, porque el cliente se cree protegido y no hay ningun equipo de
seguridad de un proveedor vigilando. La seguridad no es un anadido en este negocio: es el producto.

Este documento es un **checklist ejecutable**. Se firma en la puesta en servicio y su resultado se
adjunta al acta de aceptacion.

---

## 1. Checklist de endurecimiento

Se aplica en cada instalacion y se firma en el comisionamiento. Marcar por evidencia, no de memoria.

| # | Control | Como se verifica | Evidencia |
|---|---|---|---|
| 1 | Cortafuegos del anfitrion activo, denegar entrante por defecto | `ufw status verbose` o equivalente | Captura del estado |
| 2 | Sin acceso remoto de shell por contrasena: solo por clave, o shell deshabilitada | `sshd_config`: `PasswordAuthentication no` | Archivo de configuracion |
| 3 | **Todas** las credenciales por defecto cambiadas y registradas en el baul | Lista por dispositivo: camaras, switches, puntos de acceso, pasarela, almacenamiento | Inventario firmado |
| 4 | Doble factor en todas las cuentas con derechos administrativos | Inicio de sesion de prueba en cada interfaz | Captura del desafio |
| 5 | UPnP deshabilitado en la pasarela | Interfaz de la pasarela | Captura |
| 6 | Sin reglas de reenvio de puertos | Interfaz de la pasarela **y** escaneo externo | Resultado del escaneo |
| 7 | Gestion remota de la pasarela desde internet deshabilitada | Interfaz de la pasarela | Captura |
| 8 | Camaras: cuenta por defecto eliminada, servicios sin uso deshabilitados, funciones de nube y punto a punto desactivadas, audio desactivado salvo peticion expresa, firmware al dia en la entrega | Por camara | Lista por camara |
| 9 | Inalambrico: WPA3 o WPA2-AES, sin WPS, clave unica por segmento, gestion no expuesta por radio | Configuracion del controlador inalambrico | Exportacion de configuracion |
| 10 | Red de invitados aislada, con aislamiento entre clientes activado | Prueba desde un dispositivo invitado | Resultado de la prueba |
| 11 | Puertos de switch sin uso deshabilitados administrativamente | Configuracion del switch | Exportacion |
| 12 | Registro activo en pasarela y controlador, con retencion definida | Configuracion | Captura |
| 13 | **Escaneo externo de vulnerabilidades de la direccion publica del cliente**, con resultado limpio adjunto al acta de aceptacion | Escaneo desde fuera de la red del cliente | Informe del escaneo |
| 14 | **Acceso de administracion por interfaz desactivado en la pasarela, los switches y los puntos de acceso, en TODAS las interfaces salvo la prevista** | Ver seccion 5.1 | Lista por equipo, mas la prueba desde el controlador |

Los puntos 13 y 14 no son opcionales y no se sustituye por "revisamos la configuracion de la pasarela". El
escaneo externo es la unica comprobacion que demuestra lo que un atacante ve de verdad.

---

## 2. Identidad y control de acceso

| Control | Estandar |
|---|---|
| Cuentas | Una cuenta nombrada por miembro del hogar. **Sin cuenta administrativa compartida. Sin cuenta llamada `admin`.** |
| Doble factor | Obligatorio en el controlador, en la interfaz de gestion de red y en el almacenamiento, para toda cuenta con derechos administrativos |
| Credenciales por defecto | **Todas** cambiadas en el comisionamiento. Verificado por checklist, no de memoria |
| Politica de contrasena | Unica, generada, minimo dieciseis caracteres, almacenada solo en el baul de credenciales |
| Acceso de la empresa | **Ninguna cuenta permanente en ningun sistema de cliente.** El acceso de soporte se crea por sesion y expira. Ver seccion 4 |
| Entrega de credenciales | En el cierre del proyecto el cliente recibe el baul y un procedimiento de recuperacion administrativa. **La empresa no conserva copia** |
| Privilegio minimo | Los miembros del hogar reciben cuentas de usuario. Derechos administrativos solo donde sean genuinamente necesarios |
| Fisico | Rack o gabinete con cerradura. Acceso a consola restringido |

---

## 3. Acceso remoto, y la divulgacion honesta

### 3.1 Arquitectura

Superposicion cifrada basada en WireGuard. El telefono del cliente establece un tunel cifrado directo
contra **su propio** controlador.

- **Sin exposicion entrante.** El router no presenta ningun puerto abierto a internet, lo que elimina
  una clase entera de ataque.
- **Conexion directa entre pares** donde la red lo permite. Donde la traduccion de direcciones
  simetrica lo impide, la conexion cae a un relevo cifrado, que **no puede descifrar** el trafico que
  pasa por el.
- **Opciones de plano de control.** El servicio comercial se despliega mas rapido y exige suscripcion
  de empresa para uso comercial. El plano autoalojado de codigo abierto elimina al tercero a cambio de
  mas responsabilidad operativa. **Se ofrecen ambos, con el autoalojado por defecto** para el cliente
  cuya motivacion es la soberania.
- **Custodia de claves.** Las claves pertenecen al cliente. La empresa no conserva material de clave
  persistente de ninguna instalacion.

### 3.2 La divulgacion sobre notificaciones push

Esto se le dice al cliente con claridad y **por escrito**, porque es el unico punto donde la
afirmacion "nada sale de la casa" necesita una nota al pie.

> Las notificaciones push en Android y en iOS se entregan a traves de la infraestructura push del
> fabricante del sistema operativo. Es una propiedad arquitectonica de las plataformas moviles y
> ninguna aplicacion, de ningun proveedor, puede evitarlo sin que el telefono mantenga una conexion
> permanente en primer plano, lo cual es impracticable en iOS y costoso para la bateria en Android.

Mitigaciones aplicadas por defecto:

1. **Contenido minimo:** categoria del evento y hora. Sin imagen, sin detalle de ubicacion y sin
   nombre de camara. Lo que atraviesa el servicio push equivale a "movimiento detectado".
2. **La imagen o el clip se traen solo cuando el cliente abre la aplicacion**, y entonces viajan por
   el tunel cifrado desde su propio servidor.
3. **Alternativa solo local** para quien no quiera ningun tercero: aviso sonoro y visual en la
   vivienda mas un canal de notificacion autoalojado, alcanzable con el telefono en la red local o en
   el tunel.

La eleccion se presenta como **opcion documentada en el diseno**, no se decide en silencio en la
instalacion.

Todo competidor depende de la misma infraestructura push y ninguno lo divulga. Divulgarlo, explicar
la mitigacion y ofrecer alternativa es la demostracion de honestidad tecnica mas persuasiva
disponible en la conversacion de venta con este segmento.

---

## 4. Modelo de acceso de soporte

Pieza firma de la oferta. Se implementa con exactitud, y su implementacion vive en
`producto-cliente/stack/homeassistant/packages/sistema.yaml.j2`.

1. La empresa **no** tiene acceso permanente a ningun sistema de cliente.
2. El cliente habilita el soporte desde un control claramente etiquetado en su propio panel, o con un
   toque en la aplicacion movil.
3. Habilitarlo crea una autorizacion **limitada en el tiempo**, por defecto dos horas, implementada
   como automatizacion explicita con temporizador que revoca el acceso **al expirar, al reiniciar y
   al cancelar manualmente**.
4. Cada apertura, conexion y expiracion queda **registrada localmente** en un archivo que el cliente
   puede leer sin ayuda tecnica: `/config/registro-soporte.log`.
5. El cliente recibe **notificacion al abrirse y al cerrarse** la sesion.
6. La sesion se registra ademas en la orden de trabajo de la empresa, con nombre del tecnico, motivo
   y acciones realizadas. Es la evidencia que exige la normativa de privacidad.
7. En el cierre, y a peticion en cualquier momento, el cliente puede **retirar el acceso de forma
   permanente** con un procedimiento documentado.

La revocacion al reinicio no es un detalle: sin ella, un reinicio durante una sesion abierta dejaria
el acceso vivo sin temporizador que lo cierre. Es el fallo silencioso que convierte una promesa
contractual en una mentira.

---

## 5. Segmentacion de red

La segmentacion es lo que impide que una camara o un rele comprometidos se conviertan en acceso a los
equipos personales del hogar. Se usa **una sola red fisica con separacion logica aplicada**, que es a
la vez mas segura y mas barata que cablear en paralelo.

| Segmento | Contenido | Internet | Notas |
|---|---|---|---|
| Trusted | Telefonos, portatiles, tabletas, impresoras | Completo | Uso domestico normal |
| IoT | Reles Wi-Fi, termostatos, enchufes, paneles tactiles | Restringido: hora y puntos de actualizacion concretos | Sin ruta hacia Trusted |
| Camera | Camaras IP unicamente | Ninguno | Las camaras aceptan conexiones del grabador y **no originan ninguna** |
| Controller | Home Assistant y anfitrion de grabacion | Restringido: actualizaciones y repositorios | Alcanza IoT y Camera; alcanzable desde Trusted y desde el tunel |
| Management | Pasarela, switches, puntos de acceso, interfaces fuera de banda | Ninguno, salvo descarga deliberada de firmware | Accesible solo desde equipo administrativo o sesion de soporte autorizada. **VLAN separada de L en adelante**; en S y M se pliega en **Trusted** (ADR-009 y su enmienda) sin que las reglas dejen de aplicarse. **Controller nunca la alcanza**, en ningun nivel |
| Guest | Visitas | Completo, aislado de todo lo demas | Aislamiento entre clientes activado |

La matriz direccional completa esta en `producto-cliente/stack/red/firewall.yaml.j2`.

**La regla que mas se implementa mal:** la regla de camara es direccional y con estado. El grabador
abre la conexion hacia la camara; la camara no puede abrir una conexion hacia nada. Una regla escrita
simplemente como "bloquear la VLAN de camaras" **no** es equivalente: o rompe la grabacion, o deja
abierta la via de retorno. En el as-built se documentan como direccionales.

### 5.1 Acceso de administracion por interfaz: la pasarela tiene mas de una puerta

Dos cosas que parecen detalle y no lo son.

**La pasarela tiene una interfaz en CADA VLAN que sirve.** En una instalacion de seis segmentos, el
router responde en `10.x.10.1`, `10.x.20.1`, `10.x.30.1`, `10.x.40.1`, `10.x.50.1` y `10.x.60.1`, y
**todas son la misma administracion**. Denegar el acceso a una deja abiertas las otras cinco. Desde
el anfitrion del controlador, la administracion del router esta en `10.x.40.1`, que es literalmente
su propia puerta de enlace.

**El trafico dirigido a la pasarela no se reenvia: termina en ella**, y se filtra en una ruta
distinta de la de reenvio. UniFi, Omada y MikroTik se comportan asi. Una regla entre VLAN con
destino la IP del router **no bloquea nada**: parece que protege el acceso administrativo y no lo
toca.

De ahi salen dos obligaciones:

1. **Desactivar el acceso de administracion por interfaz** en la pasarela, los switches y los puntos
   de acceso, **en todas las interfaces salvo la prevista**. Es configuracion del equipo, no del
   cortafuegos, y es lo que cierra la puerta de verdad.
2. **Escribir la regla en la ruta de entrada**, no solo en la de reenvio. La matriz de
   `producto-cliente/stack/red/firewall.yaml.j2` tiene las dos listas separadas y explicadas.

**Prueba verificable en obra**, que consta en el acta de aceptacion: desde el anfitrion del
controlador, intentar abrir la administracion de la pasarela por **cada una** de sus direcciones. El
resultado esperado es **fallo en todas**, no solo en la primera.

```bash
# Una linea por VLAN presente. Todas deben fallar.
for v in 10 20 30 40 50 60; do
    curl -sS --max-time 5 "https://10.<octeto>.$v.1/" && echo "FALLO DE SEGURIDAD: VLAN $v responde"
done
```

Probar solo una direccion es exactamente el error que este punto corrige.

### Consecuencias practicas del segmento de camaras aislado

- **Sincronizacion horaria.** Servidor de hora **dentro** del segmento, en lugar de abrir una
  excepcion de salida. Una camara con la hora mal produce grabaciones con marca de tiempo equivocada,
  y eso destruye su valor probatorio.
- **Actualizacion de firmware.** Pasa a ser tarea manual programada del tecnico. Es argumento del
  plan de cuidado, no un defecto.
- **Las aplicaciones del fabricante no funcionaran.** Se le dice al cliente explicitamente durante el
  diseno, porque es la sorpresa mas comun en la entrega. Todo se ve por la interfaz unica del sistema.

---

## 6. Actualizaciones y gestion de versiones

| Clase | Politica | Cadencia |
|---|---|---|
| Parches de seguridad del sistema operativo | Se aplican pronto, tras validacion en banco | Dias desde la publicacion |
| Versiones de controlador y complementos | **Fijadas. Nunca automaticas.** Validadas primero en la instalacion de banco de la empresa | Revision mensual, aplicacion trimestral salvo que un problema de seguridad obligue |
| Firmware de dispositivo | Solo cuando corrige un defecto que afecta a la instalacion o cierra una vulnerabilidad. **Nunca por si mismo** | Segun necesidad |
| Cribado de cambios incompatibles | Notas de version revisadas antes de cada actualizacion; instalaciones con integraciones afectadas marcadas por adelantado | Cada ciclo |
| Reversion | **Instantanea completa antes de cada actualizacion**, con procedimiento de reversion documentado | Cada actualizacion |
| Clientes sin plan de cuidado | Version congelada en la entrega, aviso por escrito de que las actualizaciones son su responsabilidad, procedimiento documentado entregado | Al no renovar |

Esta politica es la diferencia entre un negocio sostenible y trabajo de soporte no pagado. Un stack de
codigo abierto sin gestionar se degrada, y el cliente atribuye la degradacion al instalador con
independencia de quien tomara la decision.

---

## 7. Respaldo y recuperacion

Ver `producto-cliente/stack/backup/respaldo.yaml.j2` para la implementacion. Los tres puntos que se le dicen al
cliente por escrito:

1. **El video no se respalda.** Se protege solo por redundancia de disco. Se dice explicitamente.
2. **La redundancia no es respaldo.** Protege frente a fallo de disco, no frente a borrado,
   corrupcion ni cifrado malicioso. Las instantaneas del sistema de archivos mitigan lo segundo.
3. **La clave de cifrado es del cliente.** La empresa no aloja respaldos y no conserva la clave.

Objetivo de recuperacion declarado: **reconstruccion completa desde plantilla mas respaldo en menos
de cuatro horas**. Se prueba al menos una vez al ano como parte del plan de cuidado y consta en el
registro de servicio.

---

## 8. Proteccion de datos

| Obligacion | Implementacion |
|---|---|
| Limitacion de finalidad | Informacion recogida solo para cotizacion, diseno, instalacion y soporte, con las finalidades declaradas en el contrato |
| Consentimiento | Consentimiento escrito explicito para fotografias del sitio y para el acceso de soporte. El de acceso se renueva en **cada** sesion mediante el control de habilitacion |
| Minimizacion | **La empresa no conserva video de cliente, ni transmisiones en directo, ni grabaciones, ni telemetria continua** |
| Retencion | Registros de cotizacion y diseno conservados un periodo definido y despues destruidos. Fotografias del sitio borradas al cierre salvo autorizacion del cliente |
| Salvaguardas | Estaciones de trabajo y respaldos de la empresa cifrados; baul de credenciales; **ninguna credencial de cliente en correo, chat, hojas de calculo ni notas** |
| Responsable | Una persona designada por nombre como responsable de la proteccion de la informacion personal, publicada en la politica de privacidad |
| Transparencia | Politica de privacidad publicada en frances e ingles, con que se recoge, por que, cuanto tiempo y quien puede acceder |
| Derechos del cliente | Procedimiento documentado de acceso, correccion y supresion, con plazo de respuesta comprometido |
| Transfronterizo | **Ninguna informacion personal de cliente almacenada fuera de Canada.** Las herramientas de la empresa se eligen en consecuencia |

---

## 9. Respuesta a incidentes

1. **Detectar.** Alerta del monitoreo local, aviso del cliente, o divulgacion de vulnerabilidad
   upstream que afecte a un componente desplegado.
2. **Contener.** Aislar el segmento afectado o deshabilitar el servicio afectado. El diseno de
   segmentacion convierte la contencion en un cambio de cortafuegos, no en una reconstruccion.
3. **Evaluar.** Determinar si se accedio a informacion personal. Como la empresa no conserva video de
   cliente, la mayoria de incidentes afectan a disponibilidad y no a confidencialidad, lo que reduce
   materialmente la carga de notificacion.
4. **Notificar.** Cuando haya informacion personal implicada, avisar al cliente sin demora y al
   regulador cuando se alcance el umbral legal. Quebec exige registro de incidentes de
   confidencialidad con independencia de la gravedad; confirmar umbrales y requisitos vigentes.
5. **Remediar y registrar.** Parchear, rotar credenciales, verificar y anotar el incidente en el
   registro con la cronologia y las acciones.
6. **Revisar.** Evaluar si la misma exposicion existe en otras instalaciones y aplicar la correccion a
   toda la flota **a traves de las plantillas de configuracion**, que es exactamente para lo que
   sirve la fabrica de despliegues.

El procedimiento completo esta en `herramientas-empresa/runbooks/responder-incidente-seguridad.md`.

---

## 10. Registro y auditabilidad

- Registros del controlador, la pasarela y el almacenamiento conservados localmente un periodo
  definido, dimensionado para que una pregunta de hace un mes siga teniendo respuesta.
- Registro de sesiones de soporte en un formato que **el cliente puede leer sin ayuda tecnica**.
- Cambios de configuracion versionados en este repositorio, del lado de la empresa, de modo que
  "que cambio y cuando" siempre tiene respuesta.
- Las ordenes de trabajo registran cada visita, cada sesion remota, el motivo y los cambios. Es buena
  practica y es la base probatoria si alguna vez hay una queja de privacidad.
