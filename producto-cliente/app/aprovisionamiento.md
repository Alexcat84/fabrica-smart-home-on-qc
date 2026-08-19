# Aprovisionamiento del dispositivo movil

Que queda configurado en el telefono al terminar el alta. Sirve de lista de comprobacion y de
referencia cuando alguien cambia de telefono.

## En el telefono

| Elemento | Estado esperado |
|---|---|
| Aplicacion Companion | Instalada, sesion iniciada con **cuenta nombrada** |
| Servidor | El controlador del cliente, `10.<octeto>.40.10`, por nombre local |
| Acceso remoto | Tunel configurado, **probado desde red celular** |
| Notificaciones | Permiso concedido, una de prueba recibida |
| Vistas | Las que corresponden a esa persona segun sus permisos |
| Panel anclado | En la pantalla de inicio |
| Doble factor | Obligatorio si tiene derechos administrativos |

## Lo que NO queda en el telefono

- **Ninguna credencial de la empresa.** No hay cuenta nuestra en el sistema del cliente.
- **Ninguna clave persistente que nosotros conservemos.** Las claves del tunel son del cliente.
- **Ninguna copia de video.** Se descarga bajo demanda desde su propio servidor y se sirve por el
  tunel.

## Cambio de telefono

1. Retirar el dispositivo antiguo del grupo de notificacion en el archivo de variables y regenerar.
2. Revocar la clave del tunel del dispositivo antiguo.
3. Repetir el flujo de alta con el nuevo, incluida la prueba desde red celular.

No se migra la sesion: se da de alta de nuevo. Es mas rapido que depurar por que una sesion migrada
no recibe notificaciones.

## Si el cliente pierde el telefono

1. Revocar su clave del tunel **primero**.
2. Deshabilitar la sesion de ese dispositivo en el controlador.
3. Si la cuenta tenia derechos administrativos, **rotar las credenciales compartidas**.
4. Anotarlo en la orden de trabajo: es un evento de seguridad, aunque termine bien.
