# Guia de instalacion en el telefono

Una pagina. Se hace con la persona delante, en la red de casa, y se prueba desde red celular antes de
darla por terminada.

## Orden

1. **Instalar Home Assistant** desde la tienda de la plataforma.
2. **Iniciar sesion en la red de casa.** El descubrimiento local funciona sin fricciones aqui y con
   fricciones fuera.
3. **Configurar el acceso remoto** segun el plano de control del cliente.
4. **Probar desde red celular**, con el wifi apagado. Sin esta prueba, el alta no esta terminada.
5. **Conceder permiso de notificaciones** y ver llegar una de prueba.
6. **Anclar el panel** a la pantalla de inicio.

## Por que la aplicacion no lleva nuestro nombre

Se dice, no se deja descubrir:

> La aplicacion se llama Home Assistant. Es la plataforma abierta sobre la que esta construido su
> sistema. No es nuestra, y eso es a proposito: si nosotros desaparecemos, la aplicacion sigue ahi y
> su sistema sigue funcionando exactamente igual.

Es el mismo argumento de la prueba de cancelacion, dicho en el momento en que el cliente lo puede
comprobar por si mismo.

## Lo que el cliente ve con nuestra marca

El **contenido**: tema, colores, nombres de zona, paneles, textos. Todo eso sale de
`../marca/marca.yaml` y de `../interfaz/`, y es igual en toda la flota.

Lo unico que no lleva nuestra marca es el nombre y el icono en la tienda. Es el unico limite real de
la decision, y esta declarado como tal en ADR-011.
