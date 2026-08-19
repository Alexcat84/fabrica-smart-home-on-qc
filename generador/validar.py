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
  * el ancho de banda de subida es insuficiente para los visores concurrentes
  * el octeto de red esta fuera de rango o colisiona con otro cliente
  * el paquete declarado no existe, o el inventario excede su capacidad

Uso:
    python generador/validar.py clientes/<cliente>/cliente.yaml
    python generador/validar.py --catalogo          # solo la coherencia interna del catalogo
    python generador/validar.py --todos             # todos los clientes de clientes/

Codigo de retorno: 0 si valida, 1 si hay errores.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "herramientas"))

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


def cargar_catalogo() -> dict:
    return {
        "dispositivos": cargar_yaml(RAIZ / "catalogo" / "dispositivos.yaml") or [],
        "excluidos": cargar_yaml(RAIZ / "catalogo" / "excluidos.yaml") or [],
        "proveedores": cargar_yaml(RAIZ / "catalogo" / "proveedores.yaml") or [],
        "software": cargar_yaml(RAIZ / "catalogo" / "software.yaml") or [],
    }


def cargar_paquete(id_paquete: str) -> dict | None:
    for ruta in (RAIZ / "paquetes").glob("*.yaml"):
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
                f"tiene que estar en catalogo/dispositivos.yaml antes de cotizarse."
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
                f"catalogo/dispositivos.yaml. No se instala nada que no este en el catalogo."
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
    ids = {s["id"] for s in catalogo["software"]}
    for comp in cliente.get("software_desplegado") or []:
        if comp not in ids:
            inf.error(
                f"El componente de software '{comp}' no existe en catalogo/software.yaml. "
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


def validar_ancho_banda(cliente: dict, inf: Informe) -> dict:
    try:
        resultado = calc_ancho_banda.desde_cliente(cliente)
    except ValueError as exc:
        inf.error(f"Calculo de ancho de banda imposible: {exc}")
        return {}

    if not resultado.cumple:
        inf.error(
            f"La subida es insuficiente para {resultado.visores_concurrentes} visor(es) "
            f"concurrente(s): se requieren {resultado.requerido_mbps:.2f} Mbps "
            f"(sub-streams {resultado.substream_total_mbps:.2f} + margen del hogar "
            f"{resultado.margen_hogar_mbps:.2f}) y hay {resultado.subida_disponible_mbps:.2f} Mbps "
            f"medidos. Bajar el bitrate del sub-stream, reducir visores previstos o subir el enlace."
        )
    if not resultado.cumple_principal:
        inf.aviso(
            f"Un visor que pida el stream PRINCIPAL de todas las camaras necesitaria "
            f"{resultado.principal_total_mbps:.1f} Mbps y saturaria el enlace. Es el comportamiento "
            f"esperado -el principal es bajo demanda- pero hay que explicarlo al cliente en el "
            f"diseno para que no lo interprete como averia."
        )
    if (cliente.get("red") or {}).get("cgnat"):
        inf.aviso(
            "El proveedor usa traduccion de nivel de operador: impide el tunel directo y fuerza "
            "conexion relevada, con latencia adicional. Valorar direccion estatica u otro nivel de "
            "servicio."
        )

    return {
        "subida_requerida_mbps": round(resultado.requerido_mbps, 2),
        "subida_substreams_mbps": round(resultado.substream_total_mbps, 2),
        "subida_principal_mbps": round(resultado.principal_total_mbps, 2),
        "consumo_reposo_gb_mes": round(resultado.consumo_reposo_gb_mes, 1),
        "consumo_nube_gb_mes": round(resultado.consumo_nube_equivalente_gb_mes, 1),
        "_resumen_ancho_banda": resultado.resumen(),
    }


# =================================================================================================
# Red y paquete
# =================================================================================================

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
        inf.error(f"El paquete '{id_paquete}' no existe en paquetes/.")
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
    subida = (cliente.get("red") or {}).get("subida_mbps") or 0
    if minimos.get("subida_mbps") and subida < minimos["subida_mbps"]:
        inf.error(
            f"La subida medida ({subida} Mbps) esta por debajo del minimo del paquete "
            f"{id_paquete} ({minimos['subida_mbps']} Mbps)."
        )

    return paquete


def validar_secretos_en_cliente(cliente: dict, ruta: Path, inf: Informe) -> None:
    """ADR-005: el archivo de cliente no puede contener credenciales."""
    sys.path.insert(0, str(RAIZ / "herramientas"))
    import detectar_secretos

    hallazgos = detectar_secretos.revisar_archivo(ruta)
    for numero, tipo, fragmento in hallazgos:
        inf.error(f"ADR-005: posible secreto en linea {numero} [{tipo}]: {fragmento}")


# =================================================================================================
# Catalogo: coherencia interna
# =================================================================================================

def validar_catalogo(inf: Informe) -> None:
    catalogo = cargar_catalogo()

    ids_prov = {p["id"] for p in catalogo["proveedores"]}
    vistos = set()
    for d in catalogo["dispositivos"]:
        if d["id"] in vistos:
            inf.error(f"Id de dispositivo duplicado en el catalogo: '{d['id']}'.")
        vistos.add(d["id"])

        if not d.get("control_local_sin_nube"):
            inf.error(
                f"ADR-003: '{d['id']}' esta en el catalogo de aprobados sin control local sin nube. "
                f"Deberia estar en catalogo/excluidos.yaml."
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
    validar_nomenclatura(cliente, inf)
    validar_dispositivos_contra_catalogo(cliente, catalogo, inf)
    validar_software(cliente, catalogo, inf)
    validar_octeto(cliente, inf)
    paquete = validar_paquete(cliente, inf)
    calculos.update(validar_almacenamiento(cliente, inf))
    calculos.update(validar_poe(cliente, inf))
    calculos.update(validar_ancho_banda(cliente, inf))

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
