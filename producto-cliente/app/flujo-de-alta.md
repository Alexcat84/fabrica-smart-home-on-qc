# Alta de un miembro del hogar, de principio a fin

Esta es la parte de la experiencia que mas se improvisa y peor se recuerda. Se hace igual en las
quince casas, y se hace **delante de la persona**, no antes de que llegue.

Tiempo: unos quince minutos por persona. No se acelera: la mitad del valor percibido del proyecto se
decide en estos quince minutos, porque es la primera vez que la persona toca el sistema.

Requisito previo: ADR-011. La aplicacion es la Companion de Home Assistant, no una aplicacion propia.
**Eso se dice al principio, no se deja que lo descubra en la tienda**, y se dice como lo que es: una
plataforma abierta y reconocible, que es precisamente lo que hace cierta la promesa de que el sistema
sigue funcionando si la empresa desaparece.

---

## 1. Antes de tocar el telefono

- [ ] La persona esta en `hogar` en el archivo de variables, con su `dispositivo_movil` y su
      `plataforma`, y el paquete esta regenerado y desplegado.
- [ ] Decidido si necesita derechos administrativos. **Por defecto no.** La mayoria de miembros de un
      hogar necesitan usar el sistema, no configurarlo.
- [ ] El baul de credenciales esta accesible.

---

## 2. Crear la cuenta

1. Cuenta **nombrada**, con su nombre real. Sin cuentas compartidas y sin ninguna llamada `admin`.
2. Contrasena unica, generada, minimo dieciseis caracteres. Se guarda **solo** en el baul del
   cliente. No se dicta en voz alta ni se escribe en un papel que se queda en la mesa.
3. Si tiene derechos administrativos: **doble factor obligatorio**, configurado ahora, con la persona
   delante. No "ya lo activaras".
4. Se le asignan las vistas que le corresponden.

---

## 3. Instalar la aplicacion

1. Buscar **Home Assistant** en la tienda de su plataforma.
2. Decirlo mientras lo hace: *"la aplicacion se llama Home Assistant. Es la plataforma abierta sobre
   la que esta construido su sistema. No es nuestra, y eso es a proposito: si nosotros
   desaparecemos, la aplicacion sigue ahi y su sistema sigue funcionando."*
3. Instalar e iniciar sesion **en la red de casa**, que es donde el descubrimiento funciona sin
   fricciones.

---

## 4. Establecer el tunel

1. Configurar el acceso remoto segun el plano de control elegido para ese cliente.
2. **Probarlo desde red celular**, con el wifi del telefono apagado. Esta prueba no se salta: probar
   desde el wifi de casa no demuestra nada, y es el error clasico que aparece la primera vez que la
   persona esta fuera.
3. Abrir una camara en remoto y **esperar a que cargue**. Si tarda, se explica ahora por que -se esta
   sirviendo el flujo de deteccion, y el de calidad se pide bajo demanda- en lugar de dejar que lo
   interprete como averia dentro de tres semanas.

---

## 5. Notificaciones

1. Conceder permiso de notificaciones.
2. **Enviar una de prueba y verla llegar.** Con la persona mirando el telefono.
3. Explicar el contenido minimo: *"le va a llegar la categoria y la hora. Nada mas. La imagen se
   descarga de su propio servidor cuando abre la aplicacion."*
4. Explicar la divulgacion de la infraestructura push, sin adornos: *"la notificacion viaja por la
   infraestructura de Apple o de Google. Es asi en cualquier aplicacion, de cualquier proveedor. Por
   eso el contenido es minimo. Si prefiere que no intervenga ningun tercero, podemos pasar a avisos
   solo locales; se lo explico y decide usted."*

Esta conversacion es de las que mas confianza generan de todo el proyecto. **No se abrevia.**

---

## 6. El interruptor de soporte

Se le ensena a **esta persona**, no solo al titular que firmo.

1. Ensenar donde esta el control en su panel.
2. **Encenderlo delante de ella.** Que vea la notificacion de apertura y el temporizador corriendo.
3. **Apagarlo delante de ella.** Que vea la notificacion de cierre.
4. Ensenar el registro en su propia maquina, y decir explicitamente que puede leerlo cuando quiera y
   que no hace falta saber informatica para entenderlo.
5. Decir la frase completa: *"no podemos entrar sin que usted encienda esto, y se apaga solo. Tambien
   si se reinicia el sistema."*

---

## 7. Lo que se ensena a usar

Cuatro cosas, en este orden. Mas de cuatro no se recuerdan.

1. **Encender y apagar una luz** desde la aplicacion, y **desde la pared**. Las dos. Que compruebe
   que la pared sigue mandando.
2. **Cambiar la temperatura** de una zona.
3. **Ver una camara**, en directo y un evento grabado.
4. **Poner el modo de vigilancia** al salir, si lo tiene contratado.

---

## 8. Lo que se dice antes de irse

- El sistema **no es una alarma monitoreada**. Los avisos llegan a su telefono y a nadie mas. Ningun
  servicio de emergencia se despacha automaticamente.
- Los **sensores de calidad de aire no son detectores de gas ni de monoxido**. Sus detectores de humo
  y de monoxido siguen exactamente donde estaban y no los hemos tocado.
- Si el controlador se apaga, **las luces siguen funcionando desde la pared**.
- Si deja de pagarnos, **el sistema sigue funcionando igual que el dia anterior**.

---

## 9. Al salir

- [ ] Anotado en la orden de trabajo quien se dio de alta y que se le enseno.
- [ ] Credenciales en el baul, y **ninguna copia en correo, chat, hoja de calculo ni nota**.
- [ ] `hogar` del archivo de variables al dia, y paquete regenerado si cambio algo.

---

## Baja de un miembro del hogar

1. **Deshabilitar** la cuenta, no borrarla: se conserva el historico del registro.
2. Retirar su dispositivo del grupo de notificacion en el archivo de variables y regenerar.
3. Revocar su clave del tunel.
4. Si tenia derechos administrativos, **rotar las credenciales compartidas** que hubiera podido ver.

Ver tambien `herramientas-empresa/runbooks/incorporar-miembro-hogar.md`, que es el procedimiento
interno; este documento es el guion de cara al cliente.
