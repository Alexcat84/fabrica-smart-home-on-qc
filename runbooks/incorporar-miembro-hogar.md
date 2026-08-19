# Incorporar a un miembro del hogar

## Principio

**Una cuenta nombrada por persona. Sin cuenta administrativa compartida. Sin cuenta llamada `admin`.**
Derechos administrativos solo donde sean genuinamente necesarios: la mayoria de miembros del hogar
necesitan usar el sistema, no configurarlo.

## Procedimiento

1. Anadir la persona a `hogar` en el archivo de variables del cliente:

   ```yaml
   hogar:
     - nombre: "Nombre"
       dispositivo_movil: nombre_del_dispositivo   # forma notify.mobile_app_<nombre>
       plataforma: ios                             # ios | android
       administrador: false
   ```

2. Regenerar y desplegar. El grupo de notificacion se reconstruye solo.
3. Crear la cuenta en el controlador, con nombre propio.
4. Si tiene derechos administrativos: **doble factor obligatorio**, sin excepcion.
5. Generar su contrasena: unica, generada, minimo dieciseis caracteres, guardada **solo** en el baul
   de credenciales del cliente.
6. Instalar la aplicacion movil y establecer el tunel desde su telefono.
7. Probar el acceso remoto **desde red celular**, no desde el wifi de casa: es la unica prueba que
   demuestra que el tunel funciona de verdad.

## Explicarle tres cosas, siempre

1. **Como se abre y se cierra el acceso de soporte**, y que expira solo. Es su control, no el nuestro.
2. **Que las notificaciones push pasan por la infraestructura de Apple o de Google**, que por eso el
   contenido se reduce a categoria y hora, y que la imagen se trae desde su propio servidor cuando
   abre la aplicacion. Si prefiere alerta solo local, se puede cambiar.
3. **Que el sistema no es una alarma monitoreada**: los avisos llegan a su telefono y nadie mas los
   recibe. Ningun servicio de emergencia se despacha automaticamente.

## Al salir alguien del hogar

1. Deshabilitar la cuenta, no borrarla, para conservar el historico del registro.
2. Retirar su dispositivo del grupo de notificacion en el archivo de variables y regenerar.
3. Revocar su clave del tunel.
4. Si tenia derechos administrativos, **rotar las credenciales compartidas** que hubiera podido ver.
