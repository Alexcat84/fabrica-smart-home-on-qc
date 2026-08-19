#!/usr/bin/env python3
"""Generador del paquete de cliente.

Produce `salida/<cliente>/` completo desde las plantillas versionadas mas el archivo de variables:

    salida/<cliente>/
      configuracion/          configuraciones de todos los componentes del stack
      red/                    VLAN, matriz de cortafuegos, reservas, hora local, inalambrico
      lista-de-materiales.md  materiales con proveedores por categoria
      calculos.md             almacenamiento, PoE y ancho de banda, con formula y entradas
      licencias.md            apendice de licencias de lo desplegado
      cliente/                los cuatro documentos en ingles y frances
      RESUMEN.md              indice del paquete

VALIDA ANTES DE GENERAR. Un paquete generado desde un cliente invalido es peor que ninguno: parece
correcto y no lo es.

`salida/` es artefacto derivado y no se versiona (ADR-006). Se regenera cuando cambia la plantilla o
el archivo de variables, y asi una correccion de seguridad se propaga a toda la flota.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "generador"))

import validar  # noqa: E402


def entorno_jinja() -> Environment:
    """Entorno Jinja con `StrictUndefined`.

    Deliberado: una variable ausente REVIENTA la generacion en lugar de escribir una cadena vacia en
    una configuracion que despues se despliega en casa de alguien. Un `port: ` sin valor es un
    servicio que no arranca a las once de la noche de un viernes.
    """
    return Environment(
        loader=FileSystemLoader(str(RAIZ / "plantillas")),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )


def contexto(cliente: dict, calculos: dict, textos: dict) -> dict:
    """Variables disponibles en toda plantilla."""
    ctx = dict(cliente)
    ctx.update(
        {
            "generado_en": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "calculos": calculos,
            "textos": textos,
            "textos_panel": textos.get("panel", {}),
            "paquete_def": calculos.get("_paquete", {}),
        }
    )
    return ctx


def cargar_textos(idioma: str) -> dict:
    ruta = RAIZ / "plantillas" / "homeassistant" / "textos" / f"{idioma}.yaml"
    if not ruta.is_file():
        raise SystemExit(
            f"No hay textos para el idioma '{idioma}'. Idiomas disponibles: "
            + ", ".join(p.stem for p in (RAIZ / 'plantillas' / 'homeassistant' / 'textos').glob('*.yaml'))
        )
    with open(ruta, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def render(env: Environment, plantilla: str, ctx: dict, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    contenido = env.get_template(plantilla).render(**ctx)
    destino.write_text(contenido, encoding="utf-8")


def copiar(origen: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)


# =================================================================================================
# Documentos derivados
# =================================================================================================

def lista_de_materiales(cliente: dict, catalogo: dict) -> str:
    """Lista de materiales agrupada por categoria, con proveedores desde el catalogo."""
    por_id = {d["id"]: d for d in catalogo["dispositivos"]}
    proveedores = {p["id"]: p for p in catalogo["proveedores"]}

    conteo: dict[str, int] = {}
    for item in (cliente.get("dispositivos") or []) + (cliente.get("camaras") or []):
        idc = item.get("id_catalogo")
        if idc:
            conteo[idc] = conteo.get(idc, 0) + 1

    por_categoria: dict[str, list] = {}
    for idc, n in sorted(conteo.items()):
        cat = por_id.get(idc, {})
        por_categoria.setdefault(cat.get("categoria", "sin categoria"), []).append((idc, n, cat))

    lineas = [
        f"# Lista de materiales - {cliente['cliente']['nombre']}",
        "",
        f"Paquete {cliente['paquete']} | Generado: "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "> **Los precios estan sin verificar.** El catalogo no lleva precio hasta que las cuentas de",
        "> distribucion esten abiertas y se reconstruya el coste desde la lista real (ADR-001). Esta",
        "> lista sirve para comprar, no para cotizar.",
        "",
    ]

    for categoria in sorted(por_categoria):
        lineas += [f"## {categoria.capitalize()}", ""]
        lineas += [
            "| Cant. | Id de catalogo | Fabricante | Modelo | Cert. | Proveedores |",
            "|---|---|---|---|---|---|",
        ]
        for idc, n, cat in por_categoria[categoria]:
            provs = ", ".join(
                proveedores.get(p, {}).get("nombre", p) for p in (cat.get("proveedores") or [])
            ) or "por asignar"
            lineas.append(
                f"| {n} | `{idc}` | {cat.get('fabricante') or 'por fijar'} | "
                f"{cat.get('modelo') or '**por verificar**'} | "
                f"{cat.get('certificacion') or '**por verificar**'} | {provs} |"
            )
        lineas.append("")

    pendientes = [
        idc for idc in conteo
        if por_id.get(idc, {}).get("instalable_en_caja") and not por_id.get(idc, {}).get("certificacion")
    ]
    if pendientes:
        lineas += [
            "## Verificar en recepcion antes de instalar",
            "",
            "Los siguientes van dentro de una caja electrica y su certificacion de familia todavia no",
            "esta confirmada en el catalogo. **Verificar la marca cULus, cETL o CSA impresa en la",
            "unidad fisica al recibirla** y rechazar existencias sin marca. Los fabricantes envian",
            "variantes con certificacion distinta bajo el mismo nombre de modelo segun el mercado.",
            "",
        ]
        lineas += [f"- `{idc}`" for idc in sorted(pendientes)]
        lineas.append("")

    return "\n".join(lineas)


def documento_calculos(cliente: dict, calculos: dict) -> str:
    """Calculos justificados: formula, entradas y resultado. Se adjunta a la propuesta."""
    lineas = [
        f"# Calculos de dimensionado - {cliente['cliente']['nombre']}",
        "",
        f"Paquete {cliente['paquete']} | Generado: "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Estos tres calculos se publican en cada propuesta. Los competidores citan periodos de",
        "retencion sin haberlos hecho.",
        "",
        "## 1. Almacenamiento de video",
        "",
        "```",
        "TB = (Mbps / 8) x 86400 x camaras x dias / 1e6",
        "```",
        "",
        "Regla de contraste: una camara a 8 Mbps consume unos 86 GB al dia.",
        "",
        "```",
        calculos.get("_resumen_almacenamiento", "(no calculado)"),
        "```",
        "",
        "## 2. Presupuesto de energia sobre Ethernet",
        "",
        "Suma del consumo en peor caso -incluidos infrarrojo nocturno y calefactor de invierno- mas",
        "un **40 % de holgura**. Un presupuesto ajustado produce caidas intermitentes de camara de",
        "noche, extremadamente dificiles de diagnosticar despues porque solo aparecen con frio y",
        "oscuridad.",
        "",
        "```",
        calculos.get("_resumen_poe", "(no calculado)"),
        "```",
        "",
        "## 3. Ancho de banda de subida",
        "",
        "Bitrate del sub-stream por visores concurrentes, mas margen para el trafico del hogar. La",
        "subida es la restriccion, no la bajada, y se mide en el relevamiento y no se toma del plan",
        "anunciado.",
        "",
        "```",
        calculos.get("_resumen_ancho_banda", "(no calculado)"),
        "```",
        "",
    ]
    return "\n".join(lineas)


def apendice_licencias(cliente: dict, catalogo: dict) -> str:
    """Apendice de licencias de lo realmente desplegado. Se entrega con cada instalacion."""
    por_id = {s["id"]: s for s in catalogo["software"]}
    desplegado = cliente.get("software_desplegado") or []

    lineas = [
        f"# Apendice de licencias - {cliente['cliente']['nombre']}",
        "",
        "El software de este sistema es software libre licenciado por terceros y distribuido **sin",
        "garantia de ningun tipo**. La empresa garantiza su propia mano de obra de instalacion y su",
        "configuracion; no garantiza, y no puede garantizar, el software subyacente.",
        "",
        "Politica de la empresa: **no forkeamos**. Configuramos y extendemos por los mecanismos",
        "soportados por cada proyecto. Cuando la columna *Parche publicado* esta vacia en toda la",
        "tabla -que es lo normal- no hay ningun codigo modificado en este sistema.",
        "",
        "| Componente | Version | Licencia | Repositorio | Parche publicado |",
        "|---|---|---|---|---|",
    ]
    for idc in desplegado:
        s = por_id.get(idc, {})
        lineas.append(
            f"| {s.get('nombre', idc)} | {s.get('version_fijada') or 'por fijar'} | "
            f"{s.get('licencia', 'por determinar')} | {s.get('repo_url') or '-'} | - |"
        )

    con_obligacion = [
        por_id[i] for i in desplegado
        if por_id.get(i, {}).get("obligacion_licencia") == "fuente_si_modificado"
    ]
    if con_obligacion:
        lineas += [
            "",
            "## Componentes con obligacion de fuente correspondiente",
            "",
            "Si la empresa modificase alguno de estos y lo entregase en su equipo, tendria obligacion",
            "de ofrecerle la fuente correspondiente. **No estan modificados.**",
            "",
        ]
        lineas += [f"- {s['nombre']} ({s['licencia']})" for s in con_obligacion]
        lineas.append("")

    return "\n".join(lineas)


def resumen_paquete(cliente: dict, generados: list[Path], destino_raiz: Path) -> str:
    lineas = [
        f"# Paquete generado - {cliente['cliente']['nombre']}",
        "",
        f"- **Cliente:** {cliente['cliente']['id']}",
        f"- **Paquete:** {cliente['paquete']}",
        f"- **Provincia:** {cliente['cliente']['provincia']}",
        f"- **Idioma del cliente:** {cliente['cliente']['idioma']}",
        f"- **Octeto de red:** {cliente['red']['octeto']} (10.{cliente['red']['octeto']}.x.0/24)",
        f"- **Generado:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    if cliente.get("es_ejemplo"):
        lineas += [
            "> ## ESTE ES UN CLIENTE DE DEMOSTRACION",
            ">",
            "> No corresponde a ninguna propiedad real. Sus registros de verificacion de",
            "> certificacion son **ficticios** y estan marcados como tales. No se compra nada a",
            "> partir de este paquete.",
            "",
        ]
    lineas += [
        "## Contenido",
        "",
    ]
    for ruta in sorted(generados):
        lineas.append(f"- `{ruta.relative_to(destino_raiz).as_posix()}`")
    lineas += [
        "",
        "## Siguiente paso",
        "",
        "1. Instalar fisicamente segun el inventario de red y el plan de camaras.",
        "2. Comisionar: credenciales, canal Zigbee, emparejamiento (primero los alimentados de red),",
        "   rangos de atenuacion por circuito y checklist de endurecimiento de `docs/SEGURIDAD.md`.",
        "3. Escaneo externo de puertos y adjuntar el resultado limpio al acta de aceptacion.",
        "4. Instalar la app en los moviles del hogar.",
        "5. Entregar el baul de credenciales y **no conservar copia**.",
        "",
        "Este paquete es un artefacto derivado. No se edita a mano: se corrige la plantilla o el",
        "archivo de variables y se regenera (ADR-006).",
        "",
    ]
    return "\n".join(lineas)


# =================================================================================================
# Generacion
# =================================================================================================

def generar(ruta_cliente: Path, forzar: bool = False) -> int:
    inf, calculos = validar.validar_cliente(ruta_cliente)
    inf.imprimir(str(ruta_cliente))

    if not inf.valido and not forzar:
        print()
        print("GENERACION ABORTADA: el archivo de cliente no valida.")
        print("Un paquete generado desde un cliente invalido parece correcto y no lo es.")
        print("Corrige los errores, o usa --forzar si sabes exactamente por que lo haces.")
        return 1

    cliente = validar.cargar_yaml(ruta_cliente)
    catalogo = validar.cargar_catalogo()
    textos = cargar_textos(cliente["cliente"]["idioma"])
    env = entorno_jinja()
    ctx = contexto(cliente, calculos, textos)

    destino = RAIZ / "salida" / cliente["cliente"]["id"]
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)

    generados: list[Path] = []

    def anota(p: Path) -> None:
        generados.append(p)

    # ---- Configuraciones del stack ----
    plantillas_config = [
        ("homeassistant/configuration.yaml.j2", "configuracion/homeassistant/configuration.yaml"),
        ("homeassistant/packages/sistema.yaml.j2", "configuracion/homeassistant/packages/sistema.yaml"),
        ("homeassistant/packages/iluminacion.yaml.j2", "configuracion/homeassistant/packages/iluminacion.yaml"),
        ("homeassistant/packages/clima.yaml.j2", "configuracion/homeassistant/packages/clima.yaml"),
        ("homeassistant/packages/seguridad.yaml.j2", "configuracion/homeassistant/packages/seguridad.yaml"),
        ("homeassistant/packages/energia.yaml.j2", "configuracion/homeassistant/packages/energia.yaml"),
        ("homeassistant/packages/red.yaml.j2", "configuracion/homeassistant/packages/red.yaml"),
        ("homeassistant/dashboards/panel-principal.yaml.j2", "configuracion/homeassistant/dashboards/panel-principal.yaml"),
        ("frigate/config.yaml.j2", "configuracion/frigate/config.yaml"),
        ("mosquitto/mosquitto.conf.j2", "configuracion/mosquitto/mosquitto.conf"),
        ("mosquitto/acl.j2", "configuracion/mosquitto/acl"),
        ("zigbee2mqtt/configuration.yaml.j2", "configuracion/zigbee2mqtt/configuration.yaml"),
        ("backup/respaldo.yaml.j2", "configuracion/respaldo/respaldo.yaml"),
        ("red/vlans.yaml.j2", "red/vlans.yaml"),
        ("red/firewall.yaml.j2", "red/firewall.yaml"),
        ("red/wifi.yaml.j2", "red/wifi.yaml"),
        ("red/ntp-camaras.conf.j2", "red/ntp-camaras.conf"),
    ]
    for plantilla, salida in plantillas_config:
        ruta = destino / salida
        render(env, plantilla, ctx, ruta)
        anota(ruta)

    copiar(RAIZ / "plantillas" / "mosquitto" / "passwd.plantilla",
           destino / "configuracion" / "mosquitto" / "passwd.plantilla")
    anota(destino / "configuracion" / "mosquitto" / "passwd.plantilla")

    # ---- Documentos derivados ----
    for nombre, contenido in [
        ("lista-de-materiales.md", lista_de_materiales(cliente, catalogo)),
        ("calculos.md", documento_calculos(cliente, calculos)),
        ("licencias.md", apendice_licencias(cliente, catalogo)),
    ]:
        ruta = destino / nombre
        ruta.write_text(contenido, encoding="utf-8")
        anota(ruta)

    # ---- Documentos de cliente, en ingles Y frances SIEMPRE ----
    # No solo en el idioma elegido: la propiedad puede cambiar de manos, y el documento de
    # continuidad tiene que servirle a quien venga despues.
    documentos = [
        "informe-relevamiento",
        "documento-as-built",
        "acta-de-aceptacion",
        "declaracion-de-alcance",
    ]
    dir_cliente = RAIZ / "plantillas-cliente"
    env_cliente = Environment(
        loader=FileSystemLoader(str(dir_cliente)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        # A diferencia de las plantillas de configuracion, aqui SI se recortan los bloques: son
        # documentos en Markdown que lee una persona, y las lineas en blanco que dejan los bucles
        # se ven en el resultado.
        trim_blocks=True,
        lstrip_blocks=True,
    )
    for doc in documentos:
        for idioma in ("en", "fr"):
            plantilla = f"{doc}.{idioma}.md.j2"
            if not (dir_cliente / plantilla).is_file():
                continue
            ruta = destino / "cliente" / f"{doc}.{idioma}.md"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            textos_doc = cargar_textos(idioma)
            ctx_doc = contexto(cliente, calculos, textos_doc)
            ctx_doc["idioma_documento"] = idioma
            ruta.write_text(env_cliente.get_template(plantilla).render(**ctx_doc), encoding="utf-8")
            anota(ruta)

    # ---- Resumen ----
    ruta_resumen = destino / "RESUMEN.md"
    ruta_resumen.write_text(resumen_paquete(cliente, generados, destino), encoding="utf-8")

    print()
    print(f"PAQUETE GENERADO: {destino.relative_to(RAIZ).as_posix()}/  ({len(generados) + 1} archivos)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera el paquete completo de un cliente.")
    ap.add_argument("cliente", help="Ruta del archivo de variables del cliente.")
    ap.add_argument(
        "--forzar",
        action="store_true",
        help="Genera aunque la validacion falle. Solo para depurar plantillas.",
    )
    args = ap.parse_args()

    ruta = Path(args.cliente)
    if not ruta.is_file():
        print(f"[ERROR] No existe: {ruta}")
        return 1
    return generar(ruta, forzar=args.forzar)


if __name__ == "__main__":
    sys.exit(main())
