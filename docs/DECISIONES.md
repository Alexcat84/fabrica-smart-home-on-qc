# Registro de decisiones de arquitectura (ADR)

Una entrada por decision. Formato fijo: fecha, contexto, opciones consideradas, decision, motivo,
consecuencias. Las decisiones no se borran; si una queda superada se marca `Estado: superada por ADR-NNN`
y se escribe una nueva.

Las cinco primeras entradas son las **reglas inviolables** del repositorio. No son preferencias de estilo:
cada una existe porque su incumplimiento produce un dano concreto, medible y caro. Estan implementadas
como comprobaciones ejecutables en `herramientas-empresa/validador/validar.py` y en `herramientas-empresa/detectar_secretos.py`.

---

## ADR-001 - No se inventan datos de producto

- **Fecha:** 2026-08-18
- **Estado:** vigente
- **Ambito:** `datos-maestros/`, `comercial/paquetes/`, listas de materiales generadas

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
conozca con certeza se escribe `null` y genera una fila en `docs/POR-VERIFICAR.md`. `herramientas-empresa/validador/validar.py`
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
- **Ambito:** `datos-maestros/dispositivos/`, `datos-maestros/excluidos.yaml`, validacion de cliente

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
{cULus, cETL, CSA}. Los dispositivos con marcado europeo unicamente van a `datos-maestros/excluidos.yaml`
con su motivo. `herramientas-empresa/validador/validar.py` rechaza el archivo de cliente si un dispositivo marcado
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
- **Ambito:** `datos-maestros/dispositivos/`, `datos-maestros/software-cliente.yaml`, `producto-cliente/stack/`

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
funcionar. Si la requiere, va a `datos-maestros/excluidos.yaml` con el motivo. El campo
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

### Enmienda 2026-08-19: Lutron Caseta pasa de solucion de referencia a excepcion documentada

La primera version del catalogo trataba Lutron Caseta como **la** solucion para cajas sin neutro. Esa
posicion es incompatible con esta ADR y con la regla de red unica, y se retira.

**Motivo, explicito:** Caseta introduce un **puente propietario adicional** en la propiedad, con
**registro en la nube del fabricante**. Eso choca con dos reglas a la vez:

1. **Control local sin cuenta (esta ADR).** El control local depende de una interfaz del puente cuya
   disponibilidad sin cuenta de fabricante **no esta confirmada** (fila A-02 de
   `docs/POR-VERIFICAR.md`). Mientras no lo este, la afirmacion "funciona sin internet y sin cuenta"
   no se puede sostener ante el cliente.
2. **Red unica de radio** (regla de diseno del cap. 6.2, recogida en `docs/ARQUITECTURA.md`): una red
   Zigbee por propiedad, un coordinador. Caseta anade un segundo ecosistema de radio con su propio
   puente, y cada ecosistema adicional multiplica la carga de soporte sin anadir capacidad.

**Nueva posicion:** excepcion documentada. Se especifica solo cuando el arbol de decision de ADR-008
llega a la rama "sin neutro, con espacio" y **ninguna alternativa certificada de un solo ecosistema
sirve** para ese circuito. Cuando se especifique:

- Se registra el motivo en el archivo de variables del cliente.
- Se declara al cliente por escrito, en el as-built, que hay un puente adicional y que su registro
  en la nube del fabricante es una dependencia externa del sistema.
- Queda condicionada a que A-02 se resuelva a favor. Si se resuelve en contra, Caseta pasa al
  registro de exclusion y las ramas 2 y 3 de ADR-008 son las unicas disponibles.

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
- `docs/NOMENCLATURA.md` mantiene la lista de terminos vetados y `herramientas-empresa/validador/validar.py` la verifica.

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
explicitos. `herramientas-empresa/detectar_secretos.py` corre como hook de pre-commit y bloquea el commit al
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
- **Ambito:** `producto-cliente/stack/`, `generador/`, `clientes/`, `herramientas-empresa/ansible/`

### Contexto

El modo natural de trabajar de un integrador es copiar la configuracion del ultimo cliente y editarla.
A los quince clientes hay quince variantes divergentes, ninguna documentada, y una correccion de
seguridad hay que aplicarla quince veces a mano.

### Opciones consideradas

1. Configuracion por cliente, copiada y editada. Rechazada por lo anterior.
2. Plantillas versionadas mas un archivo de variables por cliente, con generacion reproducible. **Elegida.**

### Decision

Todo lo especifico de un cliente vive en su archivo de variables. Todo lo demas vive en `producto-cliente/stack/`.
`herramientas-empresa/generador/generar.py` produce el paquete completo en `salida/<cliente>/`, que es un artefacto derivado
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

---

## ADR-008 - Iluminacion sin neutro: arbol de decision, no solucion unica

- **Fecha:** 2026-08-19
- **Estado:** vigente
- **Ambito:** `datos-maestros/dispositivos/`, relevamiento, diseno de iluminacion

### Contexto

Una parte grande del parque de vivienda de Ontario y Quebec anterior a los anos ochenta no tiene
conductor neutro en la caja del interruptor. Es el obstaculo tecnico mas frecuente del trabajo de
reforma y hay que resolverlo en el relevamiento, no el dia de la instalacion.

La primera version del catalogo trataba Lutron Caseta como **la solucion de referencia** para este
caso. Eso era un error de arquitectura: convertia un caso particular en la ruta por defecto, y
arrastraba consigo un puente propietario adicional que choca con dos reglas del repositorio.

### Opciones consideradas

1. Mantener una solucion de referencia unica. Rechazada: hace depender toda la linea de iluminacion
   en vivienda antigua de un solo fabricante y de su ruta de control local, que ni siquiera esta
   confirmada (fila A-02 de `docs/POR-VERIFICAR.md`).
2. Decidir caso por caso en obra. Rechazada: la decision se toma con el material ya comprado.
3. **Arbol de decision explicito, evaluado en el relevamiento.** Elegida.

### Decision

El caso se resuelve **en este orden**, y la primera rama que aplique es la que se especifica:

```
  Hay neutro en la caja?
   |
   +-- SI  --> INTERRUPTOR O ATENUADOR ESTANDAR
   |           Ruta por defecto. La mas amplia en catalogo, la mas barata y la que menos
   |           piezas anade. Leviton Decora Smart, Inovelli Blue 2-1, Sinope.
   |
   +-- NO --> Hay espacio en la caja?
               |
               +-- SI  --> ATENUADOR SIN NEUTRO CERTIFICADO
               |           Dispositivo disenado para el mercado norteamericano, con marca cULus,
               |           cETL o CSA verificada sobre la unidad fisica. Verificar la
               |           compatibilidad con la lampara LED concreta ANTES de cotizar, y si la
               |           carga exige modulo de bypass.
               |
               +-- NO  --> MODULO DE DOSEL
                           Montado en el dosel del luminario, con mando inalambrico de pared.
                           Requiere acceso al luminario. Certificado para Canada.
```

Circuitos multivia: dispositivos companeros **de la misma familia**. Nunca se mezclan fabricantes
dentro de un grupo multivia, en ninguna de las tres ramas.

### Motivo

Las tres ramas son soluciones legitimas para situaciones distintas. Nombrar una como *la* solucion
esconde que las otras dos existen, y empuja a comprar el producto equivocado para el caso que se
tiene delante. El relevamiento (`producto-cliente/documentos/informe-relevamiento.*`) ya recoge las tres
preguntas que este arbol necesita: neutro presente, profundidad de caja y multivia.

### Consecuencias

- La rama por defecto es la de neutro presente, no la de Lutron. La mayoria de las cajas de
  construccion posterior a los ochenta caen ahi.
- La rama sin neutro depende de la fila **A-08** de `docs/POR-VERIFICAR.md`: confirmar operacion sin
  neutro y certificacion cETL del Inovelli Blue Series 2-1, incluida la necesidad de modulo de
  bypass segun carga.
- La rama de dosel depende de la fila **A-02**, que absorbio la antigua A-03.
- Lutron Caseta deja de ser solucion de referencia y pasa a **excepcion documentada**. Ver
  ADR-003, seccion de consecuencias.

---

## ADR-009 - Management es VLAN separada de L en adelante

- **Fecha:** 2026-08-19
- **Estado:** vigente. Resuelve la discrepancia registrada como M-08.
- **Ambito:** `comercial/paquetes/`, `producto-cliente/stack/red/`, `docs/ARQUITECTURA.md`, `docs/SEGURIDAD.md`

### Contexto

El plan de negocio se contradecia a si mismo. El cap. 8.1 fija el numero de VLAN por paquete en
4 / 5 / 6 / 6 para S / M / L / XL. El cap. 8.2.1 describe Management (50) y Guest (60) como presentes
"de M en adelante", lo que daria seis en M y haria a M y L identicos en segmentacion.

La primera version del repositorio adopto una lectura provisional y abrio la fila M-08 para que el
autor lo confirmase. Esta entrada la cierra.

### Opciones consideradas

1. Seis VLAN desde M. Rechazada: contradice el recuento publicado y deja M y L sin diferencia de
   segmentacion, lo que hace la tabla de paquetes incoherente como argumento de venta.
2. Guest desde M y Management desde L. **Elegida.**
3. Management desde M y Guest desde L. Rechazada: Guest es lo que el cliente pide y ve; Management es
   una decision interna. Retrasar Guest hasta L seria retrasar una funcion visible por una razon
   invisible.

### Decision

| Paquete | VLAN | Management (50) | Guest (60) |
|---|---|---|---|
| S | 4 | Plegada en Controller | No se despliega |
| M | 5 | Plegada en Controller | **Presente** |
| L | 6 | **Presente** | Presente |
| XL | 6 o mas | Presente | Presente |

### Motivo

En S y M el numero de equipos de red gestionados es pequeno -una pasarela, un switch y uno o dos
puntos de acceso- y un segmento propio para ellos anade mantenimiento sin anadir seguridad real. A
partir de L hay varios switches y tres o mas puntos de acceso, y el segmento propio empieza a pagar
por si mismo.

Guest, en cambio, es una funcion que el cliente pide explicitamente y que sin aislamiento es un
agujero: por eso aparece antes.

### Consecuencias

- **Plegar Management NO relaja la politica de cortafuegos.** Las reglas que la nombran se aplican
  igualmente sobre las interfaces de gestion, que en S y M viven dentro del segmento Controller. Esta
  advertencia esta escrita en `producto-cliente/stack/red/firewall.yaml.j2` para que nadie la deduzca al reves.
- El acceso administrativo sigue restringido a un equipo autorizado declarado o a una sesion de
  soporte autorizada, en los cuatro niveles.
- `herramientas-empresa/validador/test_vlans.py` comprueba el recuento por paquete. La contradiccion no puede volver a
  entrar sin que una prueba falle.

### Enmienda 2026-08-19: en S y M, Management se pliega en TRUSTED, no en Controller

Los recuentos no cambian: siguen siendo **4 / 5 / 6 / 6**. Lo que cambia es **donde** se pliega la
VLAN de gestion cuando no esta separada.

**Motivo.** El anfitrion del controlador es **el objetivo de mayor valor de toda la instalacion**,
porque contiene las camaras y su grabacion. Es lo que un atacante quiere y es lo que un intruso
querria apagar. Plegar la gestion de red dentro de su segmento le daba alcance administrativo sobre
la pasarela, los switches y los puntos de acceso.

Eso convertia un compromiso del grabador en un compromiso de **la infraestructura de red entera**:
quien controle el equipo que graba podria reescribir las reglas del cortafuegos que lo contienen,
abrir un puerto o desactivar el aislamiento del segmento de camaras. La segmentacion existe
precisamente para que eso no sea posible, y la version anterior de esta ADR abria el camino en los
dos niveles mas vendidos.

Trusted no tiene ese problema. Contiene equipos personales, que son un objetivo de menor valor y que
ya tienen prohibido alcanzar Camera. El acceso administrativo sale del **equipo autorizado
declarado** en `red.equipo_administrativo`, no de cualquier telefono de la casa.

**Regla nueva, que no depende del nivel:**

> **Controller NUNCA alcanza Management.** Ni plegada ni separada, ni en S ni en XL.

Esta escrita como regla `controller_a_management` en `producto-cliente/stack/red/firewall.yaml.j2` y
tiene prueba propia en `test_vlans.py`, que la comprueba en los cuatro paquetes. No es una
consecuencia del pliegue: es una regla por si misma, y por eso se prueba por separado.

**Que no cambia:** el acceso administrativo sigue restringido al equipo autorizado o a una sesion de
soporte, y plegar la VLAN sigue sin relajar la politica. Solo reduce el numero de segmentos que hay
que mantener en una instalacion pequena.

---

## ADR-010 - La linea divisoria de licencias es la entrega, no el uso

- **Fecha:** 2026-08-19
- **Estado:** vigente
- **Ambito:** `datos-maestros/software-cliente.yaml`, `datos-maestros/software-empresa.yaml`,
  `docs/LICENCIAS.md`, apendice de licencias generado

### Contexto

Hasta ahora los 27 componentes vivian en un solo archivo, con un campo `obligacion_licencia` que
mezclaba dos cosas distintas: **que exige la licencia** y **que nos exige a nosotros en la practica**.

El caso que lo hace evidente es Ansible. Es GPL-3.0, la licencia mas copyleft del stack. En el
archivo unico aparecia con `obligacion_licencia: fuente_si_modificado`, junto a Zigbee2MQTT y
Vaultwarden, como si las tres nos obligaran a lo mismo. No es cierto: Ansible se ejecuta desde
nuestra estacion de trabajo contra el anfitrion del cliente por SSH y **no queda instalado en el
equipo que se le vende**.

Eso importa en los dos sentidos. Sobrestimar la obligacion lleva a publicar codigo que no hace falta
publicar. Subestimarla lleva a entregar un binario modificado sin la fuente correspondiente, que es
un incumplimiento real.

### Opciones consideradas

1. Un solo archivo con un campo booleano `se_entrega_al_cliente`. Rechazada: el campo se olvida al
   anadir una entrada nueva, y un descuido no produce ningun sintoma visible.
2. **Dos archivos, y la separacion fisica hace la pregunta inevitable.** Elegida. Para anadir un
   componente hay que decidir primero en cual de los dos va.
3. Deducirlo de la ruta del repositorio, `producto-cliente/` frente a `herramientas-empresa/`.
   Rechazada: no todo componente tiene plantilla, y la deduccion se rompe en cuanto uno la tenga en
   los dos sitios.

### Decision

**El disparador de la obligacion de licencia es la ENTREGA en hardware del cliente, no el uso.**

| | `software-cliente.yaml` | `software-empresa.yaml` |
|---|---|---|
| Que es | Se instala en hardware que el cliente compra y conserva | Corre en nuestra estacion de trabajo o en el banco |
| Es distribucion | **Si** | No |
| Obligacion | `aviso` o `fuente_si_modificado` segun licencia | **`ninguna`, sea cual sea la licencia** |
| Aparece en el apendice del cliente | Si | **No** |
| Componentes | 26 | 6 |

La prueba para clasificar, en una pregunta: **¿queda instalado en el equipo que el cliente se lleva?**
Si la respuesta es si, va a `software-cliente.yaml` y adquiere su obligacion. Si es no, no la tiene,
por copyleft que sea.

Ansible (GPL-3.0) y Git (GPL-2.0) estan los dos en el lado de empresa con `ninguna`, y es correcto.

### Motivo

Porque la obligacion de GPL y AGPL se activa al **transmitir** el software a un tercero. Usarlo
internamente no es transmitirlo. La AGPL anade el uso en red de una version **modificada**, que es
por lo que Vaultwarden y Grafana estan en el lado del cliente con `fuente_si_modificado` y con
`modificado_por_nosotros: false` bien visible.

### Consecuencias

- **El apendice de licencias del cliente se genera SOLO desde `software-cliente.yaml`.** Listar
  Ansible en el documento que recibe el cliente sugeriria una obligacion que no existe, y confundiria
  a quien lo lea buscando que codigo puede pedir.
- `validar.py` **rechaza** un archivo de cliente que declare como desplegado un componente de
  `software-empresa.yaml`. No es un descuido de catalogo: es afirmar que se entrega algo que no se
  entrega.
- Cada registro lleva `se_entrega_al_cliente`, `modificado_por_nosotros` y `url_parche_publicado`.
  La columna de parches del apendice esta vacia en toda la tabla, que es exactamente el objetivo de
  la politica de no forkear.
- Si un componente cruza la linea -por ejemplo, si algun dia se instalara un agente propio en el
  equipo del cliente-, se mueve de archivo y **en ese momento**, no antes, adquiere su obligacion.

---

## ADR-011 - La interfaz se entrega sobre Home Assistant, no como aplicacion propia

- **Fecha:** 2026-08-19
- **Estado:** vigente
- **Ambito:** `producto-cliente/marca/`, `producto-cliente/interfaz/`, `producto-cliente/app/`

### Decision

**La interfaz se entrega como tema, paneles y modo kiosco sobre Home Assistant y su aplicacion
Companion. No se desarrolla aplicacion propia.**

### Motivos, en orden de peso

**1. La marca de Home Assistant refuerza la propuesta de valor ante este cliente, en lugar de
restarle.**

El perfil objetivo es tecnicamente alfabetizado, averso a la suscripcion y sensible a la privacidad.
Para ese cliente, ver una plataforma abierta reconocible es una **confirmacion** de que lo que se le
vendio es cierto, no una carencia de acabado.

Una aplicacion propia sustituiria esa plataforma reconocible por una **dependencia de un proveedor
pequeno**, y contradiria directamente la prueba de cancelacion que es el eje del argumento comercial:
"si dejas de pagarnos, el sistema sigue funcionando exactamente igual que el dia anterior". Con app
propia, esa frase deja de ser cierta el dia que la empresa cierra o retira la aplicacion de la
tienda. El argumento entero se cae.

**2. Una app propia obliga a publicar y mantener en dos tiendas de forma permanente, y a rebasar
sobre el proyecto original en cada cambio aguas arriba.**

Eso es carga recurrente, no coste de desarrollo: revisiones de tienda, cambios de politica, versiones
minimas de sistema operativo, y un rebase por cada version de Home Assistant. **Inasumible antes de
tener parque instalado**, y el momento de decidirlo es antes de escribir la primera linea, no
despues.

**3. La personalizacion disponible sin bifurcar cubre la totalidad de la experiencia de uso.**

Tema, colores, tipografia, iconos, disposicion de paneles, vistas por usuario, modo kiosco, textos.
**Lo unico no personalizable es el nombre y el icono en la tienda de aplicaciones.**

### Limites que se declaran al cliente en la fase de diseno

No al final, ni cuando pregunte. En el diseno, por escrito:

1. **El modelo de permisos por usuario es de grano grueso.** Sirve para separar a los miembros de un
   hogar. **No es apto como barrera dura en escenarios de alquiler o multiinquilino**, donde la
   separacion tiene que ser de verdad. Para esos casos la separacion es de red y de sistema, no de
   interfaz.
2. **La visualizacion simultanea de varias camaras de alta resolucion en la app es inferior a un
   visor NVR dedicado.** Se explica junto al calculo de ancho de banda, porque la causa es la misma
   y el cliente que lo pregunta suele estar pensando en las dos cosas a la vez.

### Regla operativa

**Un solo tema de producto y una sola biblioteca de paneles para toda la flota.**

Lo especifico de un cliente es **la distribucion de zonas y la nomenclatura**, nunca el tema. Un tema
por cliente son quince temas que mantener a los quince clientes, y una correccion visual que hay que
aplicar quince veces.

`validar.py` **rechaza** un archivo de cliente que defina tema propio.

### Disparadores para reabrir

Esta decision se revisa, no se hereda, si ocurre cualquiera de estas tres:

- **Mas de 150 instalaciones activas.** A esa escala la carga de mantener una app se reparte entre
  suficientes clientes.
- **Contrato comercial que exija marca propia.** Un cliente de tamano suficiente puede pagar la
  diferencia.
- **Cambio aguas arriba que rompa el uso profesional**, por ejemplo que la aplicacion Companion deje
  de permitir el modo kiosco o el tema personalizado.

### Consecuencias

- `producto-cliente/marca/` e `interfaz/` son **capa separada y parametrizada**. Ninguna plantilla
  del stack contiene color, tipografia ni texto de marca: los toma de ahi.
- Por eso una migracion futura seria **cambio de envase, no rehacer el producto**. Si algun dia se
  cruza un disparador, lo que hay que reescribir es la capa de presentacion, no la logica ni los
  datos.
- `producto-cliente/app/` documenta el flujo de alta de un miembro del hogar de principio a fin, que
  es la parte de la experiencia que mas se improvisa y peor se recuerda.
