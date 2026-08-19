#!/usr/bin/env python3
"""Validador del archivo de cliente.

Este script es donde las reglas inviolables de `docs/DECISIONES.md` dejan de ser texto y pasan a ser
comprobaciones que bloquean. Se ejecuta ANTES de comprar nada.

Rechaza el archivo de cliente si:

  * un dispositivo no esta en el catalogo                                        (ADR-001)
  * un dispositivo `instalable_en_caja` no tiene certificacion canadiense        (ADR-002)
  * un dispositivo del catalogo no tiene control local sin nube                  (ADR-003)
  * aparece un termino de seguridad de vida en cualquier nombre                  (ADR-004)
  * el calculo de almacenamiento no alcanza la retencion pedida
  * el presupuesto PoE no tiene 40 % de holgura
  * el ancho de banda de subida no cubre los DOS escenarios: vista general, y un visor
    escalando una camara a stream principal
  * una camara no tiene bitrate de sub-stream medido, ni en catalogo ni en cliente (M-13)
  * el octeto de red esta fuera de rango o colisiona con otro cliente
  * el paquete declarado no existe, o el inventario excede su capacidad

Uso:
    python herramientas-empresa/validador/validar.py clientes/<cliente>/cliente.yaml
    python herramientas-empresa/validador/validar.py --catalogo          # solo la coherencia interna del catalogo
    python herramientas-empresa/validador/validar.py --todos             # todos los clientes de clientes/

Codigo de retorno: 0 si valida, 1 si hay errores.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import jsonschema
import yaml

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "herramientas-empresa" / "calculadoras"))
sys.path.insert(0, str(RAIZ / "herramientas-empresa"))

import calc_almacenamiento  # noqa: E402
import calc_ancho_banda  # noqa: E402
import calc_poe  # noqa: E402

CERTIFICACIONES_VALIDAS = {"cULus", "cETL", "CSA"}

# ADR-004. Lista de docs/NOMENCLATURA.md, seccion 1. Se compara contra nombres normalizados.
TERMINOS_VETADOS = {
    "smoke", "humo", "fumee", "fumée",
    "fire", "fuego", "incendie",
    "carbon_monoxide", "monoxide", "monoxido", "monoxyde",
    "gas_detect", "detector_gas", "gaz",
    "alarm", "alarma", "alarme",
    "panic", "panico",
    "emergency", "emergencia", "urgence",
    "life_safety", "seguridad_de_vida", "securite_vie",
}

# Terminos que contienen una subcadena vetada pero son legitimos. Se comprueban primero.
EXCEPCIONES_VETO = {
    "calidad_aire", "air_quality", "qualite_air",
    "disuasion", "deterrent", "dissuasion",
}

OCTETO_MIN, OCTETO_MAX = 1, 254

DIAS_VALIDEZ_MEDICION = 90
"""Cuanto vale una medicion de subida antes de repetirla.

No es arbitrario: en tres meses el cliente puede haber cambiado de plan y el proveedor su politica de
subida. Un diseno apoyado en una medicion vieja promete un visionado remoto que puede haber dejado de
caber, y nadie se entera hasta que el cliente esta fuera de casa mirando el telefono.
"""

MARCA_EJEMPLO = "EJEMPLO-NO-REAL"
"""Marcador de verificacion ficticia.

Solo se acepta en un archivo con `es_ejemplo: true`. Existe para que el cliente de demostracion
pueda validar de extremo a extremo sin que nadie confunda su registro de verificacion con uno real,
y para que ese patron no pueda filtrarse a un cliente de verdad por copiar y pegar.
"""


@dataclass
class Informe:
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def error(self, mensaje: str) -> None:
        self.errores.append(mensaje)

    def aviso(self, mensaje: str) -> None:
        self.avisos.append(mensaje)

    @property
    def valido(self) -> bool:
        return not self.errores

    def imprimir(self, etiqueta: str) -> None:
        if self.errores:
            print(f"\n{etiqueta}: {len(self.errores)} ERROR(ES)")
            for e in self.errores:
                print(f"  [ERROR] {e}")
        if self.avisos:
            print(f"\n{etiqueta}: {len(self.avisos)} aviso(s)")
            for a in self.avisos:
                print(f"  [aviso] {a}")
        if not self.errores and not self.avisos:
            print(f"\n{etiqueta}: correcto, sin errores ni avisos.")
        elif not self.errores:
            print(f"\n{etiqueta}: VALIDA (con avisos).")


# =================================================================================================
# Carga
# =================================================================================================

def cargar_yaml(ruta: Path):
    with open(ruta, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


DATOS = RAIZ / "datos-maestros"


def cargar_dispositivos() -> list[dict]:
    """Un archivo por categoria. Se concatenan en el orden alfabetico del nombre de archivo."""
    dispositivos: list[dict] = []
    for ruta in sorted((DATOS / "dispositivos").glob("*.yaml")):
        dispositivos.extend(cargar_yaml(ruta) or [])
    return dispositivos


def cargar_catalogo() -> dict:
    """El software va en dos archivos porque la obligacion de licencia depende de si se entrega.

    `software` los une para quien solo necesita buscar por id; `software_cliente` y
    `software_empresa` se conservan separados para lo que si depende de la distincion.
    """
    cliente = cargar_yaml(DATOS / "software-cliente.yaml") or []
    empresa = cargar_yaml(DATOS / "software-empresa.yaml") or []
    return {
        "dispositivos": cargar_dispositivos(),
        "excluidos": cargar_yaml(DATOS / "excluidos.yaml") or [],
        "proveedores": cargar_yaml(DATOS / "proveedores.yaml") or [],
        "software_cliente": cliente,
        "software_empresa": empresa,
        "software": cliente + empresa,
    }


def cargar_paquete(id_paquete: str) -> dict | None:
    for ruta in (RAIZ / "comercial" / "paquetes").glob("*.yaml"):
        datos = cargar_yaml(ruta)
        if datos and datos.get("id") == id_paquete:
            return datos
    return None


# =================================================================================================
# ADR-004: terminos de seguridad de vida
# =================================================================================================

def contiene_termino_vetado(texto: str) -> str | None:
    """Devuelve el termino vetado encontrado, o None."""
    if not texto:
        return None
    normalizado = str(texto).lower().replace("-", "_").replace(" ", "_")
    for permitido in EXCEPCIONES_VETO:
        normalizado = normalizado.replace(permitido, "")
    for vetado in TERMINOS_VETADOS:
        # Comparacion por palabra completa dentro del identificador, para que `alarma` salte y
        # `calamar` no.
        partes = normalizado.split("_")
        if vetado in partes or vetado == normalizado:
            return vetado
        # Terminos compuestos como `life_safety`.
        if "_" in vetado and vetado in normalizado:
            return vetado
    return None


def validar_nomenclatura(cliente: dict, inf: Informe) -> None:
    campos = []
    for d in cliente.get("dispositivos") or []:
        campos.append(("dispositivo", d.get("nombre"), d.get("nombre")))
        campos.append(("dispositivo", d.get("nombre"), d.get("area")))
        campos.append(("dispositivo", d.get("nombre"), d.get("nombre_cliente")))
    for c in cliente.get("camaras") or []:
        campos.append(("camara", c.get("nombre"), c.get("nombre")))
        campos.append(("camara", c.get("nombre"), c.get("area")))
        campos.append(("camara", c.get("nombre"), c.get("nombre_cliente")))
    for e in cliente.get("escenas") or []:
        campos.append(("escena", e.get("id"), e.get("nombre")))

    for tipo, duenio, valor in campos:
        vetado = contiene_termino_vetado(valor)
        if vetado:
            inf.error(
                f"ADR-004: el {tipo} '{duenio}' usa el termino vetado '{vetado}' en '{valor}'. "
                f"Ningun nombre puede sugerir funcion de seguridad de vida. "
                f"Ver docs/NOMENCLATURA.md, seccion 1."
            )


# =================================================================================================
# ADR-001, ADR-002, ADR-003: catalogo
# =================================================================================================

def validar_dispositivos_contra_catalogo(cliente: dict, catalogo: dict, inf: Informe) -> None:
    por_id = {d["id"]: d for d in catalogo["dispositivos"]}
    excluidos = {e["id"] for e in catalogo["excluidos"]}

    entradas = [
        ("dispositivo", d) for d in (cliente.get("dispositivos") or [])
    ] + [
        ("camara", c) for c in (cliente.get("camaras") or [])
    ]

    for tipo, item in entradas:
        nombre = item.get("nombre", "(sin nombre)")
        id_cat = item.get("id_catalogo")

        if not id_cat:
            inf.error(
                f"ADR-001: el {tipo} '{nombre}' no declara `id_catalogo`. Todo lo que se instala "
                f"tiene que estar en datos-maestros/dispositivos/ antes de cotizarse."
            )
            continue

        if id_cat in excluidos:
            motivo = next(e["motivo"] for e in catalogo["excluidos"] if e["id"] == id_cat)
            inf.error(
                f"El {tipo} '{nombre}' usa '{id_cat}', que esta en el REGISTRO DE EXCLUSION. "
                f"Motivo: {motivo.strip()}"
            )
            continue

        if id_cat not in por_id:
            inf.error(
                f"ADR-001: el {tipo} '{nombre}' referencia '{id_cat}', que no existe en "
                f"datos-maestros/dispositivos/. No se instala nada que no este en el catalogo."
            )
            continue

        cat = por_id[id_cat]

        # ADR-002: certificacion canadiense para instalacion fija.
        #
        # La certificacion puede venir de dos sitios, en este orden:
        #   1. El catalogo, cuando la familia ya se verifico de forma general.
        #   2. El registro de verificacion POR SKU del propio archivo de cliente, que es como
        #      funciona el proceso real: la marca se comprueba sobre la unidad fisica en recepcion,
        #      porque los fabricantes envian variantes distintas del mismo nombre de modelo segun
        #      el mercado. Ese registro es un hecho del proyecto, no una suposicion del catalogo.
        if cat.get("instalable_en_caja"):
            verificacion = item.get("certificacion_verificada") or {}
            cert = verificacion.get("marca") or cat.get("certificacion")
            origen = "cliente" if verificacion.get("marca") else "catalogo"

            if not cert:
                inf.error(
                    f"ADR-002: '{id_cat}' ({nombre}) es instalable en caja electrica y su "
                    f"certificacion esta sin verificar (null). No se puede especificar hasta "
                    f"confirmar la marca cULus, cETL o CSA sobre la unidad fisica en recepcion. "
                    f"Registrarla en `certificacion_verificada` de este dispositivo, o verificar la "
                    f"familia en el catalogo. Ver docs/POR-VERIFICAR.md, fila A-01."
                )
            elif cert not in CERTIFICACIONES_VALIDAS:
                inf.error(
                    f"ADR-002: '{id_cat}' ({nombre}) declara certificacion '{cert}', que no es "
                    f"una marca canadiense valida ({', '.join(sorted(CERTIFICACIONES_VALIDAS))})."
                )
            elif origen == "cliente":
                faltan = [c for c in ("verificado_por", "fecha", "sku") if not verificacion.get(c)]
                if faltan:
                    inf.error(
                        f"ADR-002: la verificacion de '{id_cat}' ({nombre}) esta incompleta: falta "
                        f"{', '.join(faltan)}. Una verificacion sin autor, fecha y SKU no es "
                        f"trazable y no vale ante un inspector."
                    )
                elif verificacion.get("verificado_por") == MARCA_EJEMPLO:
                    if not cliente.get("es_ejemplo"):
                        inf.error(
                            f"'{id_cat}' ({nombre}) usa una verificacion marcada como "
                            f"{MARCA_EJEMPLO} en un cliente que no declara `es_ejemplo: true`. "
                            f"Esto es un registro ficticio copiado del cliente de demostracion: "
                            f"sustituirlo por la verificacion real antes de comprar."
                        )
                    else:
                        inf.aviso(
                            f"'{id_cat}' ({nombre}): verificacion FICTICIA de demostracion."
                        )
                else:
                    inf.aviso(
                        f"'{id_cat}' ({nombre}): certificacion {cert} verificada en recepcion por "
                        f"{verificacion['verificado_por']} el {verificacion['fecha']} "
                        f"(SKU {verificacion['sku']}). Promover al catalogo si la familia entera "
                        f"queda confirmada."
                    )

        # ADR-003: control local sin nube.
        if not cat.get("control_local_sin_nube"):
            inf.error(
                f"ADR-003: '{id_cat}' ({nombre}) no tiene control local sin nube. Ningun "
                f"componente puede requerir cuenta de fabricante para funcionar."
            )

        # ADR-001: dato no verificado. Es aviso, no error: el diseno puede avanzar, la compra no.
        if not cat.get("verificado"):
            inf.aviso(
                f"'{id_cat}' ({nombre}) tiene `verificado: false`. Confirmar SKU, certificacion y "
                f"precio antes de emitir la orden de compra."
            )


def validar_software(cliente: dict, catalogo: dict, inf: Informe) -> None:
    """ADR-010: lo que se despliega en casa del cliente sale de `software-cliente.yaml`.

    Declarar una herramienta interna como desplegada no es un descuido de catalogo: es afirmar que
    se entrega algo que no se entrega, y por tanto declarar una obligacion de licencia que no
    existe -o peor, ocultar que si se entrega algo que deberia estar en la otra lista.
    """
    ids_cliente = {s["id"] for s in catalogo["software_cliente"]}
    ids_empresa = {s["id"] for s in catalogo["software_empresa"]}

    for comp in cliente.get("software_desplegado") or []:
        if comp in ids_cliente:
            continue
        if comp in ids_empresa:
            inf.error(
                f"ADR-010: '{comp}' esta en datos-maestros/software-empresa.yaml, que es "
                f"herramienta interna y no se entrega al cliente. Si de verdad se instala en su "
                f"equipo, muevelo a software-cliente.yaml: en ese momento adquiere su obligacion de "
                f"licencia, y no antes."
            )
        else:
            inf.error(
                f"El componente de software '{comp}' no existe en datos-maestros/software-cliente.yaml. "
                f"Sin entrada de catalogo no hay licencia declarada ni apendice que entregar."
            )


# =================================================================================================
# Dimensionado
# =================================================================================================

def validar_almacenamiento(cliente: dict, inf: Informe) -> dict:
    try:
        resultado = calc_almacenamiento.desde_cliente(cliente)
    except ValueError as exc:
        inf.error(f"Calculo de almacenamiento imposible: {exc}")
        return {}

    instalado = (cliente.get("almacenamiento") or {}).get("vigilancia_tb")
    if instalado is None:
        inf.error(
            "No se declara `almacenamiento.vigilancia_tb`. La retencion prometida no se puede "
            "sostener sin dimensionar el disco."
        )
    elif instalado < resultado.tb_con_margen:
        ret = cliente.get("retencion", {})
        inf.error(
            f"El almacenamiento no alcanza la retencion pedida: se requieren "
            f"{resultado.tb_con_margen:.2f} TB (continua {ret.get('continua_dias')} d + eventos "
            f"{ret.get('eventos_dias')} d, con {resultado.margen_aplicado:.0%} de margen) y hay "
            f"{instalado} TB instalados. Subir el disco, acortar la retencion o bajar el bitrate."
        )

    return {
        "almacenamiento_tb": round(resultado.tb_con_margen, 2),
        "almacenamiento_continua_tb": round(resultado.tb_continua, 2),
        "almacenamiento_eventos_tb": round(resultado.tb_eventos, 2),
        "almacenamiento_gb_dia": round(resultado.gb_por_dia, 1),
        "_resumen_almacenamiento": resultado.resumen(),
    }


def validar_poe(cliente: dict, inf: Informe) -> dict:
    presupuesto = (cliente.get("poe") or {}).get("presupuesto_switch_w")
    if not presupuesto:
        inf.error(
            "No se declara `poe.presupuesto_switch_w`. Sin el no se puede comprobar la holgura del "
            "40 %, y un presupuesto PoE justo produce caidas de camara de noche en invierno."
        )
        return {}

    try:
        resultado = calc_poe.desde_cliente(cliente)
    except ValueError as exc:
        inf.error(f"Calculo PoE imposible: {exc}")
        return {}

    if not resultado.cumple:
        inf.error(
            f"El presupuesto PoE no tiene el 40 % de holgura exigido: peor caso "
            f"{resultado.peor_caso_w:.1f} W, requerido {resultado.requerido_w:.1f} W, switch "
            f"{resultado.presupuesto_switch_w:.1f} W (holgura real {resultado.holgura_real:.1%}). "
            f"Subir el switch o repartir la carga en dos."
        )
    if resultado.hay_estimaciones:
        inf.aviso(
            "El calculo PoE usa consumos tipicos por tipo, no datos de ficha tecnica. Sustituirlos "
            "antes de comprometer el switch (ADR-001)."
        )

    return {
        "poe_peor_caso_w": round(resultado.peor_caso_w, 1),
        "poe_requerido_w": round(resultado.requerido_w, 1),
        "poe_holgura_real": round(resultado.holgura_real, 3),
        "_resumen_poe": resultado.resumen(),
    }


def validar_ancho_banda(cliente: dict, catalogo: dict, inf: Informe) -> dict:
    """Tres escenarios. Los dos primeros son vinculantes; el tercero advierte (ADR-012).

    1. Cuadricula remota: N visores concurrentes sobre sub-stream.
    2. Apertura de una camara sobre flujo medio, o sobre principal si la camara solo publica dos
       flujos. Es lo que la gente hace treinta segundos despues de abrir la cuadricula.
    3. Apertura sobre principal: excepcion bajo demanda. Se advierte y no se rechaza, porque
       rechazar obligaria a contratar enlaces que nadie necesita el 99 % del tiempo.
    """
    try:
        resultado = calc_ancho_banda.desde_cliente(cliente, catalogo["dispositivos"])
    except calc_ancho_banda.SubstreamSinMedir as exc:
        inf.error(f"ADR-001: {exc}")
        return {}
    except ValueError as exc:
        inf.error(f"Calculo de ancho de banda imposible: {exc}")
        return {}

    if not resultado.cumple_cuadricula:
        inf.error(
            f"ESCENARIO 1 (cuadricula remota): la subida es insuficiente para "
            f"{resultado.visores_concurrentes} visor(es) concurrente(s). Se requieren "
            f"{resultado.requerido_cuadricula_mbps:.2f} Mbps (sub-streams "
            f"{resultado.sub_total_mbps:.2f} + margen del hogar "
            f"{resultado.margen_hogar_mbps:.2f}) y hay {resultado.subida_disponible_mbps:.2f} Mbps "
            f"medidos. Bajar el bitrate del sub-stream, reducir visores previstos o subir el enlace."
        )

    if not resultado.cumple_apertura:
        via = (
            "sobre el stream PRINCIPAL, porque esa camara solo publica dos flujos"
            if resultado.apertura_usa_principal
            else "sobre el flujo medio"
        )
        inf.error(
            f"ESCENARIO 2 (apertura de una camara): si un visor abre "
            f"'{resultado.camara_de_apertura}' {via}, el salto de "
            f"{resultado.salto_apertura_mbps:.2f} Mbps eleva lo requerido a "
            f"{resultado.requerido_apertura_mbps:.2f} Mbps, y hay "
            f"{resultado.subida_disponible_mbps:.2f} Mbps. El cliente hara esto en cuanto vea algo "
            f"en la cuadricula, asi que no es un caso extremo. Bajar el bitrate del flujo de "
            f"apertura, usar camaras de tres flujos, reducir visores o subir el enlace. NO se "
            f"resuelve transcodificando en el servidor (ADR-012)."
        )

    if not resultado.cabe_principal:
        inf.aviso(
            f"ESCENARIO 3 (apertura sobre stream principal): pediria "
            f"{resultado.requerido_principal_mbps:.2f} Mbps y hay "
            f"{resultado.subida_disponible_mbps:.2f} Mbps. Es una EXCEPCION BAJO DEMANDA y por eso "
            f"no se rechaza: el principal se pide a mano para revisar algo concreto y va lento. "
            f"Explicarlo al cliente en el diseno para que no lo interprete como averia."
        )

    if resultado.camaras_de_dos_flujos:
        inf.aviso(
            f"Camaras que solo publican dos flujos, sin intermedio util: "
            f"{', '.join(resultado.camaras_de_dos_flujos)}. Abrirlas en remoto sirve el stream "
            f"principal, que es mucho mas caro en subida. Es la penalizacion real de esos modelos."
        )

    if resultado.hay_datos_de_catalogo:
        inf.aviso(
            "Hay bitrates de flujo tomados del catalogo y no medidos en este sitio. Confirmarlos "
            "contra el firmware real de la camara instalada antes de prometer visionado remoto "
            "(M-13, M-14)."
        )

    if (cliente.get("red") or {}).get("cgnat"):
        inf.aviso(
            "El proveedor usa traduccion de nivel de operador: impide el tunel directo y fuerza "
            "conexion relevada, con latencia adicional. Valorar direccion estatica u otro nivel de "
            "servicio."
        )

    return {
        "subida_requerida_mbps": round(resultado.requerido_cuadricula_mbps, 2),
        "subida_requerida_apertura_mbps": round(resultado.requerido_apertura_mbps, 2),
        "subida_requerida_principal_mbps": round(resultado.requerido_principal_mbps, 2),
        "subida_substreams_mbps": round(resultado.sub_total_mbps, 2),
        "subida_salto_apertura_mbps": round(resultado.salto_apertura_mbps, 2),
        "subida_apertura_usa_principal": resultado.apertura_usa_principal,
        "_resumen_ancho_banda": resultado.resumen(),
    }


# =================================================================================================
# Red y paquete
# =================================================================================================

# Claves de presentacion que pertenecen al producto, no al cliente (ADR-011).
CLAVES_DE_MARCA_PROHIBIDAS = ("tema", "theme", "paleta", "marca", "colores", "tipografia")


def validar_tema_unico(cliente: dict, inf: Informe) -> None:
    """ADR-011: un solo tema de producto y una sola biblioteca de paneles para toda la flota.

    Lo especifico del cliente es la distribucion de zonas y la nomenclatura, nunca el tema. Un tema
    por cliente son quince temas que mantener a los quince clientes, y una correccion visual que hay
    que aplicar quince veces.
    """
    for clave in CLAVES_DE_MARCA_PROHIBIDAS:
        if clave in cliente:
            inf.error(
                f"ADR-011: el archivo de cliente define `{clave}`. La capa de marca es del producto "
                f"y es una sola para toda la flota: vive en producto-cliente/marca/marca.yaml. "
                f"Lo especifico de este cliente es la distribucion de zonas y la nomenclatura. Si "
                f"hace falta una variante visual, la decision es de producto y va al ADR, no a un "
                f"archivo de cliente."
            )

    interfaz = cliente.get("interfaz")
    if isinstance(interfaz, dict):
        for clave in CLAVES_DE_MARCA_PROHIBIDAS:
            if clave in interfaz:
                inf.error(
                    f"ADR-011: el archivo de cliente define `interfaz.{clave}`. Mismo motivo: el "
                    f"tema es del producto, no del cliente."
                )


def validar_medicion_de_subida(cliente: dict, inf: Informe) -> None:
    """La subida se MIDE en el relevamiento; no se copia del folleto del proveedor.

    Antes, el validador comparaba los tres escenarios contra `subida_mbps` y nada impedia que ahi se
    escribiera la velocidad anunciada del plan. Solo lo decia un comentario, y un comentario no
    rechaza nada. Un enlace de cable vendido como 15 Mbps entrega a menudo bastante menos en subida,
    que es justo la direccion que importa.
    """
    red = cliente.get("red") or {}

    if "subida_mbps" in red and "subida_medida_mbps" not in red:
        inf.error(
            "El archivo de cliente usa `subida_mbps` sin procedencia. Sustituir por "
            "`subida_medida_mbps`, `fecha_medicion` y `metodo_medicion`: el diseno se apoya en ese "
            "numero y tiene que constar de donde sale."
        )
        return

    medida = red.get("subida_medida_mbps")
    if medida is None:
        inf.error(
            "No se declara `red.subida_medida_mbps`. Es la subida MEDIDA en el sitio, contra la que "
            "se comprueban los tres escenarios de ancho de banda (ADR-012)."
        )
        return

    metodo = red.get("metodo_medicion")
    if not metodo:
        inf.error(
            "No se declara `red.metodo_medicion`. Sin saber como se midio, el numero no vale para "
            "sostener una promesa de visionado remoto."
        )
    elif metodo == "anunciada_por_proveedor":
        inf.error(
            "`metodo_medicion: anunciada_por_proveedor` NO es una medicion: es el folleto. La subida "
            "se mide en el relevamiento, con el enlace del sitio. El valor anunciado se puede "
            "guardar aparte en `subida_anunciada_mbps`, que sirve para ensenarle al cliente la "
            "diferencia, pero el diseno no se apoya en el."
        )
    elif metodo == "informe_del_proveedor":
        inf.aviso(
            "La subida viene de un informe del proveedor, no de una prueba en el sitio. Sirve para "
            "cotizar, pero conviene confirmarla en el relevamiento antes de comprometer visionado "
            "remoto concurrente."
        )

    fecha = red.get("fecha_medicion")
    if not fecha:
        inf.error(
            "No se declara `red.fecha_medicion`. Una medicion sin fecha no se puede caducar, y una "
            "medicion vieja promete un enlace que quiza ya no existe."
        )
        return

    try:
        medido_el = date.fromisoformat(str(fecha))
    except ValueError:
        inf.error(f"`red.fecha_medicion` = '{fecha}' no es una fecha ISO valida (AAAA-MM-DD).")
        return

    dias = (date.today() - medido_el).days
    if dias < 0:
        inf.error(f"`red.fecha_medicion` = {fecha} esta en el futuro.")
    elif dias > DIAS_VALIDEZ_MEDICION:
        inf.error(
            f"La medicion de subida tiene {dias} dias y caduca a los {DIAS_VALIDEZ_MEDICION}. "
            f"Repetirla antes de disenar: en tres meses el cliente puede haber cambiado de plan y el "
            f"proveedor su politica de subida."
        )
    elif dias > DIAS_VALIDEZ_MEDICION - 15:
        inf.aviso(
            f"La medicion de subida tiene {dias} dias y caduca a los {DIAS_VALIDEZ_MEDICION}. "
            f"Conviene repetirla antes de cerrar el diseno."
        )

    anunciada = red.get("subida_anunciada_mbps")
    if anunciada and medida < anunciada * 0.7:
        inf.aviso(
            f"La subida medida ({medida} Mbps) esta un {100 - medida / anunciada * 100:.0f} % por "
            f"debajo de la anunciada ({anunciada} Mbps). Merece la pena ensenarselo al cliente: suele "
            f"ser el mejor argumento de por que hace falta otro nivel de servicio."
        )


def validar_octeto(cliente: dict, inf: Informe) -> None:
    octeto = (cliente.get("red") or {}).get("octeto")
    if octeto is None:
        inf.error("No se declara `red.octeto`. Se asigna desde el registro de la empresa.")
        return
    if not isinstance(octeto, int) or not OCTETO_MIN <= octeto <= OCTETO_MAX:
        inf.error(f"`red.octeto` = {octeto} esta fuera del rango {OCTETO_MIN}-{OCTETO_MAX}.")
        return

    # Colision con otro cliente: dos sitios con el mismo octeto rompen la superposicion de soporte
    # cuando un tecnico esta conectado a ambos.
    mio = cliente.get("cliente", {}).get("id")
    for ruta in (RAIZ / "clientes").glob("*/cliente.yaml"):
        otro = cargar_yaml(ruta)
        if not otro:
            continue
        if otro.get("cliente", {}).get("id") == mio:
            continue
        if (otro.get("red") or {}).get("octeto") == octeto:
            inf.error(
                f"COLISION DE OCTETO: '{otro.get('cliente', {}).get('id')}' ya usa el octeto "
                f"{octeto}. Dos sitios con el mismo direccionamiento colisionan cuando un tecnico "
                f"esta conectado a ambos por la superposicion de soporte."
            )


def validar_paquete(cliente: dict, inf: Informe) -> dict | None:
    id_paquete = cliente.get("paquete")
    paquete = cargar_paquete(id_paquete)
    if not paquete:
        inf.error(f"El paquete '{id_paquete}' no existe en comercial/paquetes/.")
        return None

    cap = paquete.get("capacidad", {})
    n_disp = len(cliente.get("dispositivos") or [])
    n_cam = len(cliente.get("camaras") or [])

    maximo = cap.get("dispositivos_automatizados_max")
    if maximo and n_disp > maximo:
        inf.aviso(
            f"{n_disp} dispositivos exceden el maximo de {maximo} del paquete {id_paquete}. "
            f"Valorar subir de nivel: el dimensionado del controlador y de la malla lo asume."
        )

    cam_max = cap.get("camaras_max")
    if cam_max and n_cam > cam_max:
        inf.aviso(
            f"{n_cam} camaras exceden el maximo de {cam_max} del paquete {id_paquete}."
        )

    minimos = paquete.get("internet_minimo", {})
    subida = (cliente.get("red") or {}).get("subida_medida_mbps") or 0
    if minimos.get("subida_mbps") and subida < minimos["subida_mbps"]:
        inf.error(
            f"La subida medida ({subida} Mbps) esta por debajo del minimo del paquete "
            f"{id_paquete} ({minimos['subida_mbps']} Mbps)."
        )

    return paquete


def validar_secretos_en_cliente(cliente: dict, ruta: Path, inf: Informe) -> None:
    """ADR-005: el archivo de cliente no puede contener credenciales."""
    sys.path.insert(0, str(RAIZ / "herramientas-empresa"))
    import detectar_secretos

    hallazgos = detectar_secretos.revisar_archivo(ruta)
    for numero, tipo, fragmento in hallazgos:
        inf.error(f"ADR-005: posible secreto en linea {numero} [{tipo}]: {fragmento}")


# =================================================================================================
# Esquemas: un campo mal escrito se rechaza, no se ignora
# =================================================================================================

ESQUEMAS = RAIZ / "datos-maestros" / "esquemas"

# (archivo de esquema, como localizar los registros que valida)
APLICACION_ESQUEMAS = [
    ("dispositivo.schema.json", "dispositivos"),
    ("proveedor.schema.json", "proveedores"),
    ("excluido.schema.json", "excluidos"),
    ("software.schema.json", "software"),
]


def cargar_esquema(nombre: str) -> dict:
    with open(ESQUEMAS / nombre, encoding="utf-8") as fh:
        return json.load(fh)


def validar_contra_esquemas(catalogo: dict, inf: Informe) -> None:
    """Aplica JSON Schema a cada registro de los datos maestros.

    Por que esto existe: `certificacon: CSA` no es un error de sintaxis YAML. Es un campo que nadie
    lee, y un dispositivo que parece certificado sin estarlo. `additionalProperties: false` convierte
    ese fallo silencioso en un rechazo ruidoso, que es lo unico que sirve.
    """
    for archivo, clave in APLICACION_ESQUEMAS:
        try:
            esquema = cargar_esquema(archivo)
        except FileNotFoundError:
            inf.error(f"Falta el esquema datos-maestros/esquemas/{archivo}.")
            continue

        validador = jsonschema.Draft202012Validator(esquema)
        for registro in catalogo.get(clave, []):
            identificador = registro.get("id", "(sin id)") if isinstance(registro, dict) else "?"
            for fallo in sorted(validador.iter_errors(registro), key=lambda e: list(e.path)):
                ruta = ".".join(str(x) for x in fallo.path) or "(raiz)"
                inf.error(
                    f"Esquema {archivo}: '{identificador}', campo `{ruta}`: {fallo.message}"
                )


def validar_esquemas_de_paquetes(inf: Informe) -> None:
    try:
        esquema = cargar_esquema("paquete.schema.json")
    except FileNotFoundError:
        inf.error("Falta el esquema datos-maestros/esquemas/paquete.schema.json.")
        return
    validador = jsonschema.Draft202012Validator(esquema)
    for ruta_paquete in sorted((RAIZ / "comercial" / "paquetes").glob("*.yaml")):
        datos = cargar_yaml(ruta_paquete)
        for fallo in sorted(validador.iter_errors(datos), key=lambda e: list(e.path)):
            campo = ".".join(str(x) for x in fallo.path) or "(raiz)"
            inf.error(
                f"Esquema paquete.schema.json: {ruta_paquete.name}, campo `{campo}`: {fallo.message}"
            )


# =================================================================================================
# Catalogo: coherencia interna
# =================================================================================================

def validar_esquema_de_red(cliente: dict, inf: Informe) -> None:
    """Aplica cliente-red.schema.json al bloque `red` del archivo de cliente."""
    try:
        esquema = cargar_esquema("cliente-red.schema.json")
    except FileNotFoundError:
        inf.error("Falta el esquema datos-maestros/esquemas/cliente-red.schema.json.")
        return
    validador = jsonschema.Draft202012Validator(esquema)
    for fallo in sorted(validador.iter_errors(cliente.get("red") or {}), key=lambda e: list(e.path)):
        campo = ".".join(str(x) for x in fallo.path) or "(raiz)"
        inf.error(f"Esquema cliente-red.schema.json: campo `red.{campo}`: {fallo.message}")


def validar_catalogo(inf: Informe) -> None:
    catalogo = cargar_catalogo()

    validar_contra_esquemas(catalogo, inf)
    validar_esquemas_de_paquetes(inf)

    ids_prov = {p["id"] for p in catalogo["proveedores"]}
    vistos = set()
    for d in catalogo["dispositivos"]:
        if d["id"] in vistos:
            inf.error(f"Id de dispositivo duplicado en el catalogo: '{d['id']}'.")
        vistos.add(d["id"])

        if not d.get("control_local_sin_nube"):
            inf.error(
                f"ADR-003: '{d['id']}' esta en el catalogo de aprobados sin control local sin nube. "
                f"Deberia estar en datos-maestros/excluidos.yaml."
            )
        for prov in d.get("proveedores") or []:
            if prov not in ids_prov:
                inf.error(f"'{d['id']}' referencia el proveedor inexistente '{prov}'.")

        vetado = contiene_termino_vetado(d.get("id"))
        if vetado:
            inf.error(f"ADR-004: el id de catalogo '{d['id']}' contiene el termino vetado '{vetado}'.")

    ids_soft = {s["id"] for s in catalogo["software"]}
    for s in catalogo["software"]:
        for sust in s.get("sustituible_por") or []:
            if sust not in ids_soft:
                inf.error(f"'{s['id']}' referencia el sustituto inexistente '{sust}'.")

    sin_certificar = [
        d["id"] for d in catalogo["dispositivos"]
        if d.get("instalable_en_caja") and not d.get("certificacion")
    ]
    if sin_certificar:
        inf.aviso(
            f"{len(sin_certificar)} dispositivos instalables en caja siguen sin certificacion "
            f"verificada. No se pueden especificar en un cliente hasta confirmarla "
            f"(docs/POR-VERIFICAR.md, fila A-01)."
        )


# =================================================================================================
# Orquestacion
# =================================================================================================

def validar_cliente(ruta: Path) -> tuple[Informe, dict]:
    inf = Informe()
    cliente = cargar_yaml(ruta)
    if not cliente:
        inf.error(f"{ruta} esta vacio o no es YAML valido.")
        return inf, {}

    catalogo = cargar_catalogo()
    calculos: dict = {}

    validar_secretos_en_cliente(cliente, ruta, inf)
    validar_esquema_de_red(cliente, inf)
    validar_nomenclatura(cliente, inf)
    validar_dispositivos_contra_catalogo(cliente, catalogo, inf)
    validar_software(cliente, catalogo, inf)
    validar_tema_unico(cliente, inf)
    validar_medicion_de_subida(cliente, inf)
    validar_octeto(cliente, inf)
    paquete = validar_paquete(cliente, inf)
    calculos.update(validar_almacenamiento(cliente, inf))
    calculos.update(validar_poe(cliente, inf))
    calculos.update(validar_ancho_banda(cliente, catalogo, inf))

    if paquete:
        calculos["_paquete"] = paquete

    return inf, calculos


def main() -> int:
    ap = argparse.ArgumentParser(description="Valida un archivo de cliente contra las reglas del repositorio.")
    ap.add_argument("cliente", nargs="?", help="Ruta del archivo de variables del cliente.")
    ap.add_argument("--catalogo", action="store_true", help="Valida solo la coherencia del catalogo.")
    ap.add_argument("--todos", action="store_true", help="Valida todos los clientes de clientes/.")
    ap.add_argument("--detalle", action="store_true", help="Imprime los calculos justificados.")
    args = ap.parse_args()

    if args.catalogo:
        inf = Informe()
        validar_catalogo(inf)
        inf.imprimir("CATALOGO")
        return 0 if inf.valido else 1

    rutas: list[Path]
    if args.todos:
        rutas = sorted((RAIZ / "clientes").glob("*/cliente.yaml"))
        if not rutas:
            print("No hay clientes en clientes/.")
            return 0
    elif args.cliente:
        rutas = [Path(args.cliente)]
    else:
        ap.error("Indica un archivo de cliente, o usa --catalogo o --todos.")
        return 1

    fallo = False
    for ruta in rutas:
        if not ruta.is_file():
            print(f"[ERROR] No existe: {ruta}")
            fallo = True
            continue
        inf, calculos = validar_cliente(ruta)
        inf.imprimir(str(ruta))
        if args.detalle:
            for clave in ("_resumen_almacenamiento", "_resumen_poe", "_resumen_ancho_banda"):
                if clave in calculos:
                    print()
                    print(calculos[clave])
        if not inf.valido:
            fallo = True

    print()
    print("RESULTADO:", "RECHAZADO" if fallo else "VALIDADO")
    return 1 if fallo else 0


if __name__ == "__main__":
    sys.exit(main())
