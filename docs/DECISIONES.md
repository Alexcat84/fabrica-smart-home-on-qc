# Registro de decisiones de arquitectura (ADR)

Una entrada por decision. Formato fijo: fecha, contexto, opciones consideradas, decision, motivo,
consecuencias. Las decisiones no se borran; si una queda superada se marca `Estado: superada por ADR-NNN`
y se escribe una nueva.

Las cinco primeras entradas son las **reglas inviolables** del repositorio. No son preferencias de estilo:
cada una existe porque su incumplimiento produce un dano concreto, medible y caro. Estan implementadas
como comprobaciones ejecutables en `generador/validar.py` y en `herramientas/detectar_secretos.py`.

---

## ADR-001 - No se inventan datos de producto

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** `catalogo/`, `paquetes/`, listas de materiales generadas

### Contexto

El catalogo alimenta directamente la lista de materiales, la propuesta comercial y el documento as-built.
Un numero de parte, un precio o una afirmacion de certificacion que nadie verifico se propaga sin friccion
desde un archivo YAML hasta un contrato firmado y hasta una inspeccion electrica.

El plan de negocio de origen (`docs/fuente/Smart-Home-Business-Plan-ON-QC.docx`) declara explicitamente
que sus cifras estan indicadas "to the best available knowledge" y marca con `(V)` todo lo que exige
confirmacion contra la fuente primaria. El catalogo hereda esa condicion.

### Opciones consideradas

1. Poblar el catalogo con los modelos y precios mas probables y corregir despues. Rechazada: un dato
   plausible es indistinguible de un dato verificado una vez escrito, y nadie vuelve a revisarlo.
2. Dejar el catalogo vacio hasta tener datos verificados. Rechazada: bloquea todo el trabajo de
   plantillas, generador y validacion, que solo necesita la estructura y las familias.
3. Poblar por **familia de producto** con todos los campos inciertos en `null`, marca `verificado: false`
   y una fila obligatoria en `docs/POR-VERIFICAR.md`. **Elegida.**

### Decision

Cada entrada del catalogo lleva `certificacion`, `fuente_url` y `verificado: false`. Todo dato que no se
conozca con certeza se escribe `null` y genera una fila en `docs/POR-VERIFICAR.md`. `generador/validar.py`
rechaza cualquier archivo de cliente que dependa de un dato inventado.

### Motivo

Un dato inventado en este repositorio se convierte mas tarde en una inspeccion electrica rechazada, en
una cotizacion que no se puede sostener o en una reclamacion de seguro denegada.

### Consecuencias

- El catalogo arranca con muchos `null`. Es el estado correcto, no un defecto.
- `docs/POR-VERIFICAR.md` es una cola de trabajo real, ordenada por urgencia, no un apendice.
- La verificacion se hace contra el SKU fisico en recepcion, no contra una pagina web.

---

## ADR-002 - Certificacion canadiense obligatoria para instalacion fija

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** `catalogo/dispositivos.yaml`, `catalogo/excluidos.yaml`, validacion de cliente

### Contexto

El Codigo Electrico Canadiense exige que todo dispositivo instalado dentro de una caja electrica o
conectado a tension de linea lleve una marca de certificacion canadiense visible: cULus, cETL o CSA.
El marcado europeo CE no es equivalente y no es aceptable. Los fabricantes envian variantes con
certificacion distinta bajo el mismo nombre de modelo segun el mercado de destino.

### Opciones consideradas

1. Evaluar caso por caso en obra. Rechazada: la decision se toma bajo presion de tiempo y con el
   material ya comprado.
2. Aceptar dispositivos con marcado europeo cuando sean tecnicamente equivalentes. Rechazada: la
   equivalencia tecnica es irrelevante frente al inspector y frente a la aseguradora.
3. Regla dura en el catalogo, con registro de exclusion explicito y motivo. **Elegida.**

### Decision

Ningun dispositivo entra al catalogo como `instalable_en_caja: true` sin `certificacion` en
{cULus, cETL, CSA}. Los dispositivos con marcado europeo unicamente van a `catalogo/excluidos.yaml`
con su motivo. `generador/validar.py` rechaza el archivo de cliente si un dispositivo marcado
`instalable_en_caja` no tiene certificacion.

### Motivo

Instalar un dispositivo no certificado en una caja electrica canadiense expone al cliente a una falla
de inspeccion y a una denegacion de seguro, y al instalador a la responsabilidad resultante. Es una
categoria donde la decision correcta cuesta dinero y hay que preciarla.

### Consecuencias

- Buena parte del catalogo de aficionado queda fuera. Esa eliminacion es el punto, no un efecto colateral.
- Los dispositivos rechazados (Sonoff ZBMINIL2, modulos de rele Aqara, SKU europeos) se registran una vez
  y no se vuelven a evaluar.
- La verificacion final es sobre la marca impresa en la unidad fisica, en recepcion.

---

## ADR-003 - Ningun componente puede depender de la nube de un fabricante

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** `catalogo/dispositivos.yaml`, `catalogo/software.yaml`, `plantillas/`

### Contexto

La propuesta de valor completa del negocio es que el cliente es dueno del servidor, que los datos no
salen de la propiedad y que no hay suscripcion obligatoria a ningun tercero. Un solo componente que
exija cuenta de fabricante para operar destruye esa afirmacion y la convierte en una nota al pie.

### Opciones consideradas

1. Permitir dependencia de nube en funciones secundarias. Rechazada: la frontera es imposible de
   explicar al cliente y el fabricante puede mover la funcion de secundaria a esencial en una actualizacion.
2. Prohibicion total, con registro de exclusion. **Elegida.**

### Decision

Ningun componente del stack ni del catalogo puede requerir una cuenta en la nube de un fabricante para
funcionar. Si la requiere, va a `catalogo/excluidos.yaml` con el motivo. El campo
`control_local_sin_nube: true` es obligatorio en todo dispositivo del catalogo.

### Motivo

Sin esta regla, la respuesta honesta a "que sale de mi casa" deja de ser "nada excepto la notificacion
a tu propio telefono", que es la posicion de venta que sostiene todo el modelo.

### Consecuencias

- Se documenta una unica excepcion arquitectonica, inevitable y divulgada por escrito: las notificaciones
  push de Android e iOS pasan por la infraestructura del fabricante del sistema operativo movil. Se mitiga
  reduciendo el contenido de la notificacion a categoria y hora, y se ofrece alerta solo local como
  alternativa documentada. Ver `docs/SEGURIDAD.md` y la declaracion de alcance del cliente.
- La actualizacion de firmware de camaras pasa a ser tarea manual programada del tecnico. Es un argumento
  del plan de cuidado, no un defecto.

---

## ADR-004 - No hay fuego: exclusion total de seguridad de vida

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** todo el repositorio, sin excepcion

### Contexto

Los sistemas de seguridad de vida en Canada se rigen por normas separadas, exigen tecnicos certificados
aparte y acarrean una categoria de exposicion legal que una integradora pequena no puede absorber.

### Opciones consideradas

1. Incluir deteccion de humo y CO como funcion "informativa". Rechazada: la etiqueta informativa no
   sobrevive al momento en que un cliente confia en ella durante una emergencia.
2. Exclusion declarada, escrita en cada propuesta y en cada contrato, y verificada mecanicamente en el
   repositorio. **Elegida.**

### Decision

Nada en este repositorio toca deteccion de incendio, gas, monoxido de carbono, alerta medica ni ningun
otro sistema de seguridad de vida. Ninguna plantilla, automatizacion, entidad o etiqueta puede sugerir
funcion de seguridad de vida. Si lo hace, es un defecto y se corrige.

Consecuencias concretas ya implementadas:

- Los sensores de calidad de aire llevan en `notas` la negacion explicita de funcion de deteccion de gas.
- Las sirenas se documentan como dispositivo disuasorio, nunca como alarma, y tienen prohibido el patron
  temporal-tres, reservado a la senalizacion de evacuacion.
- No se instala rele, atenuador ni modulo alguno en un circuito compartido con detectores interconectados.
- No se automatizan enclavamientos de ventilacion exigidos por codigo.
- `docs/NOMENCLATURA.md` mantiene la lista de terminos vetados y `generador/validar.py` la verifica.

### Motivo

Declarar la frontera con claridad protege a la empresa y, presentada correctamente, aumenta la confianza
del cliente en lugar de reducirla.

### Consecuencias

- La deteccion de intrusion se ofrece solo como alerta local notificada al propietario, con sirenas
  opcionales. No hay central de monitoreo, no hay despacho policial, no hay contrato de recepcion de alarmas.
- Toda propuesta y todo contrato incluyen la declaracion de alcance con las exclusiones textuales.

---

## ADR-005 - Ningun secreto en el repositorio

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** todo el repositorio y todo paquete generado

### Contexto

El repositorio contiene la configuracion de cada instalacion de cliente. Una contrasena de camara, una
clave de WireGuard o un token de API filtrado en el historial de git es un incidente de confidencialidad
que afecta a una casa concreta y que git conserva para siempre aunque el archivo se borre despues.

### Opciones consideradas

1. Disciplina y revision manual. Rechazada: falla exactamente el dia que hay prisa.
2. Cifrado con `ansible-vault` mas deteccion automatica antes del commit. **Elegida.**

### Decision

Contrasenas, claves y tokens van cifrados con `ansible-vault` o quedan como marcadores de posicion
explicitos. `herramientas/detectar_secretos.py` corre como hook de pre-commit y bloquea el commit al
detectar material sensible. Las credenciales reales viven en el baul de credenciales del cliente
(Vaultwarden), que se entrega al cliente en el cierre del proyecto; la empresa no conserva copia.

### Motivo

La empresa no tiene acceso permanente a ningun sistema de cliente. Un secreto en el repositorio
contradice ese modelo y convierte al repositorio en el punto unico de compromiso de toda la flota.

### Consecuencias

- `.gitignore` excluye `*.key`, `*.pem`, `.vault_pass`, `.env` y familia.
- El hook se instala con `git config core.hooksPath .githooks`, sin dependencias externas.
- `.pre-commit-config.yaml` se entrega ademas para quien tenga `pre-commit` instalado.
- Los archivos de cliente en `clientes/` usan marcadores del tipo `CAMBIAR-EN-COMISIONAMIENTO`.

---

## ADR-006 - El repositorio es una fabrica de despliegues, no un almacen de configuraciones

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** `plantillas/`, `generador/`, `clientes/`, `ansible/`

### Contexto

El modo natural de trabajar de un integrador es copiar la configuracion del ultimo cliente y editarla.
A los quince clientes hay quince variantes divergentes, ninguna documentada, y una correccion de
seguridad hay que aplicarla quince veces a mano.

### Opciones consideradas

1. Configuracion por cliente, copiada y editada. Rechazada por lo anterior.
2. Plantillas versionadas mas un archivo de variables por cliente, con generacion reproducible. **Elegida.**

### Decision

Todo lo especifico de un cliente vive en su archivo de variables. Todo lo demas vive en `plantillas/`.
`generador/generar.py` produce el paquete completo en `salida/<cliente>/`, que es un artefacto derivado
y no se commitea. Nada se construye a mano en casa del cliente. No hay copos de nieve.

### Motivo

Objetivo declarado y verificable: reconstruccion completa de un controlador destruido, desde plantilla
mas respaldo, en menos de cuatro horas, sin conocimiento tribal.

### Consecuencias

- `salida/` esta en `.gitignore`.
- Una correccion de seguridad se aplica en la plantilla y se propaga a toda la flota por regeneracion.
- Las versiones de contenedores y complementos van fijadas y las actualizaciones automaticas deshabilitadas.

---

## ADR-007 - El material de origen se versiona dentro del repositorio

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** `docs/fuente/`

### Contexto

El catalogo, los paquetes, la matriz de firewall y el checklist de endurecimiento se sembraron desde el
plan de negocio y desde el prompt de arranque. Sin el original a mano, en seis meses nadie puede
distinguir que dato vino de una fuente y cual se anadio despues.

### Decision

`docs/fuente/` conserva `Smart-Home-Business-Plan-ON-QC.docx` (plan v1.0, 18 ago 2026) y
`prompt-claude-code-startup.md`, versionados y sin modificar. Toda entrada del catalogo cuya procedencia
sea el plan de negocio lo declara en `notas` cuando no exista URL primaria.

### Motivo

Trazabilidad del dato hasta su origen, que es precisamente lo que ADR-001 exige poder demostrar.
