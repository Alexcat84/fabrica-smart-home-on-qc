# Atender una sesion de soporte

## Lo primero, y no es negociable

**No puedes entrar hasta que el cliente abra la sesion.** No es una norma interna que se pueda saltar
con prisa: no existe credencial permanente de la empresa en el sistema del cliente. Si el cliente no
activa el interruptor, no hay ruta. Eso *es* el producto.

## Procedimiento

1. **El cliente abre la sesion** desde el control de su panel o desde la aplicacion movil.
2. Confirmar que esta abierta. La empresa recibe la señal; no la crea.
3. Anotar en la orden de trabajo, **antes de conectarse**: tecnico, motivo y que se va a tocar.
4. Conectarse por el tunel.
5. Hacer **solo** lo acordado. Cualquier hallazgo adicional se anota y se propone; no se arregla de
   paso sin decirlo, aunque sea rapido.
6. Los cambios de configuracion se hacen en el repositorio y se regeneran. **No se edita a mano en el
   anfitrion** (ADR-006): un cambio manual desaparece en la siguiente regeneracion y, mientras tanto,
   nadie sabe que existe.
7. Cerrar la sesion explicitamente al terminar, sin esperar a que expire.
8. Completar la orden de trabajo con las acciones realizadas.

## Que ve el cliente, y por que importa

- Notificacion al abrirse la sesion y al cerrarse.
- El temporizador corriendo en su panel.
- Cada apertura, conexion y expiracion escrita en `/config/registro-soporte.log`, en su propia
  maquina, en un formato que puede leer **sin ayuda tecnica**.

Nunca le pidas al cliente que deje la sesion abierta "por si acaso". Que expire sola es exactamente
lo que compro.

## Revocaciones automaticas

La autorizacion cae en cuatro situaciones, y las cuatro estan implementadas:

1. Expiracion del temporizador (dos horas por defecto).
2. Cancelacion manual por el propietario.
3. **Reinicio del controlador**: automatizacion de Home Assistant, mas una unidad de systemd por si
   Home Assistant no llega a arrancar.
4. Cierre normal al terminar la sesion.

La tercera es la que se olvida al implementarla, y es la que convierte una promesa contractual en una
mentira: sin ella, un reinicio durante una sesion abierta dejaria el acceso vivo sin temporizador que
lo cierre.

## Si el cliente pide retirar el acceso de forma permanente

Se hace, se documenta y no se discute. El procedimiento esta en el documento as-built, seccion de
credenciales. Es un derecho del cliente y forma parte de lo que se le vendio.

## Registro obligatorio

La sesion se anota tambien en la orden de trabajo de la empresa, con tecnico, motivo y acciones. Es
la evidencia que exige la normativa de privacidad y la base probatoria si alguna vez hay una queja.
