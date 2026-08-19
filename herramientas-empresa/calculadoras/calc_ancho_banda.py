#!/usr/bin/env python3
"""Calculadora de ancho de banda de subida.

Tres roles de flujo, y cada uno tiene un trabajo distinto (ADR-012):

    principal   grabacion local. NO se sirve por el tunel salvo peticion explicita con advertencia
    medio       apertura de UNA camara en remoto
    sub         deteccion y cuadricula remota

Y tres escenarios, que es lo que de verdad hace la gente:

    1. Cuadricula remota   N visores concurrentes, todos sobre `sub`        -> RECHAZA si no cabe
    2. Apertura de camara  uno de ellos abre una camara sobre `medio`       -> RECHAZA si no cabe
    3. Apertura a principal  esa misma apertura, pero sobre `principal`     -> ADVIERTE, no rechaza

El escenario 3 no rechaza porque es una **excepcion bajo demanda**: el cliente pide calidad de
grabacion para revisar algo concreto, sabiendo que va a ir lento. Rechazar por el obligaria a
contratar enlaces que nadie necesita el 99 % del tiempo. Pero se advierte, y la advertencia se
imprime en el documento de calculos que ve el cliente, para que no lo interprete como averia.

**Si la camara solo publica dos flujos**, no hay `medio`: el escenario 2 usa el `principal` y
**rechaza en consecuencia**. Esa es la penalizacion real de una camara de dos flujos, y es la razon
de que `streams_soportados` sea un dato de catalogo y no un detalle.

PROHIBIDO resolver esto transcodificando en el servidor. Ver ADR-012: el equipo es clase N100 y el
transcodificado consume el presupuesto de inferencia que necesita la deteccion.

El bitrate de cada flujo se lee del **registro del dispositivo**, no de una constante. Si nadie lo ha
medido, se levanta `SubstreamSinMedir` y el validador rechaza el cliente (fila M-14).

Sin dependencias externas. Pruebas en `test_calc_ancho_banda.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MARGEN_HOGAR_MBPS = 5.0
"""Subida reservada al uso normal del hogar: videollamadas, respaldos, juego en linea.

No es un colchon de cortesia. Sin el, la primera videollamada de trabajo del cliente convive con el
visionado remoto y una de las dos se degrada; el cliente culpara al sistema que acaba de instalar.
"""


class SubstreamSinMedir(ValueError):
    """Falta el bitrate de algun flujo, en el catalogo y en el archivo de cliente.

    No se sustituye por un valor por defecto a proposito: de el depende si el visionado remoto que se
    promete cabe en la subida contratada. Un valor inventado convierte una promesa comercial en una
    suposicion (ADR-001).
    """


@dataclass
class CamaraAB:
    """Una camara con sus tres flujos resueltos, y la procedencia de cada dato."""

    nombre: str
    principal_mbps: float
    sub_mbps: float
    medio_mbps: float | None
    streams_soportados: int
    origen_sub: str
    origen_medio: str

    @property
    def tiene_flujo_medio(self) -> bool:
        return self.streams_soportados >= 3 and self.medio_mbps is not None

    @property
    def bitrate_de_apertura_mbps(self) -> float:
        """Lo que se sirve al abrir ESTA camara en remoto.

        Con tres flujos es el medio. Con dos, no hay eleccion: es el principal, y se nota.
        """
        return self.medio_mbps if self.tiene_flujo_medio else self.principal_mbps

    @property
    def salto_de_apertura_mbps(self) -> float:
        """Coste adicional de abrir esta camara: el visor deja de pedir su sub."""
        return max(0.0, self.bitrate_de_apertura_mbps - self.sub_mbps)

    @property
    def salto_a_principal_mbps(self) -> float:
        return max(0.0, self.principal_mbps - self.sub_mbps)


def _resolver(valor_cliente, valor_catalogo, origen_cliente="cliente", origen_catalogo="catalogo"):
    if valor_cliente is not None:
        return float(valor_cliente), origen_cliente
    if valor_catalogo is not None:
        return float(valor_catalogo), origen_catalogo
    return None, "desconocido"


def resolver_camara(camara_cliente: dict, registro_catalogo: dict | None) -> CamaraAB:
    """Construye la camara resolviendo cada flujo contra el catalogo.

    Prioridad: el archivo de cliente manda sobre el catalogo, porque es una medicion del sitio
    concreto con el firmware que tiene esa camara.
    """
    cat = registro_catalogo or {}
    nombre = camara_cliente.get("nombre", "(sin nombre)")

    sub, origen_sub = _resolver(
        camara_cliente.get("bitrate_substream_mbps"), cat.get("substream_bitrate_mbps")
    )
    if sub is None:
        raise SubstreamSinMedir(
            f"La camara '{nombre}' no tiene bitrate de SUB-STREAM ni en el archivo de cliente "
            f"(`bitrate_substream_mbps`) ni en el catalogo (`substream_bitrate_mbps` de "
            f"'{camara_cliente.get('id_catalogo')}'). Medirlo en banco por modelo y firmware. No se "
            f"supone un valor: de el depende si el visionado remoto concurrente que se promete cabe "
            f"en la subida contratada (M-13)."
        )

    streams = camara_cliente.get("streams_soportados", cat.get("streams_soportados"))
    if streams is None:
        raise SubstreamSinMedir(
            f"La camara '{nombre}' no declara `streams_soportados`, ni en el archivo de cliente ni "
            f"en el catalogo. Sin ese dato no se sabe si al abrirla en remoto se sirve un flujo "
            f"intermedio o directamente el principal, y la diferencia entre las dos cosas decide si "
            f"el enlace del sitio aguanta. Medirlo en banco (M-14)."
        )
    streams = int(streams)

    medio, origen_medio = _resolver(
        camara_cliente.get("bitrate_medio_mbps"), cat.get("stream_medio_bitrate_mbps")
    )
    if streams >= 3 and medio is None:
        raise SubstreamSinMedir(
            f"La camara '{nombre}' declara {streams} flujos pero no tiene bitrate del flujo MEDIO. "
            f"Medirlo en banco (`stream_medio_bitrate_mbps`), o poner `streams_soportados: 2` si de "
            f"verdad no publica un tercer flujo util: en ese caso el calculo usa el principal y "
            f"rechaza en consecuencia, que es el resultado correcto."
        )

    return CamaraAB(
        nombre=nombre,
        principal_mbps=float(camara_cliente["bitrate_principal_mbps"]),
        sub_mbps=sub,
        medio_mbps=medio,
        streams_soportados=streams,
        origen_sub=origen_sub,
        origen_medio=origen_medio,
    )


@dataclass
class ResultadoAnchoBanda:
    # Escenario 1: cuadricula remota
    sub_total_mbps: float
    requerido_cuadricula_mbps: float
    cumple_cuadricula: bool

    # Escenario 2: apertura de una camara (flujo medio, o principal si solo hay dos flujos)
    salto_apertura_mbps: float
    camara_de_apertura: str
    apertura_usa_principal: bool
    requerido_apertura_mbps: float
    cumple_apertura: bool

    # Escenario 3: apertura sobre principal, excepcion bajo demanda
    salto_principal_mbps: float
    camara_del_salto_principal: str
    requerido_principal_mbps: float
    cabe_principal: bool

    margen_hogar_mbps: float
    subida_disponible_mbps: float
    visores_concurrentes: int
    cumple: bool

    hay_datos_de_catalogo: bool
    camaras_de_dos_flujos: list[str] = field(default_factory=list)
    detalle: list[dict] = field(default_factory=list)

    def resumen(self) -> str:
        e1 = "CUMPLE" if self.cumple_cuadricula else "NO CUMPLE"
        e2 = "CUMPLE" if self.cumple_apertura else "NO CUMPLE"
        e3 = "cabe" if self.cabe_principal else "NO cabe"
        lineas = [
            "CALCULO DE ANCHO DE BANDA DE SUBIDA",
            f"  Visores concurrentes previstos : {self.visores_concurrentes}",
            f"  Subida disponible (medida)     : {self.subida_disponible_mbps:7.2f} Mbps",
            f"  Margen para el hogar           : {self.margen_hogar_mbps:7.2f} Mbps",
            "",
            "  Escenario 1 - cuadricula remota (todos los visores sobre sub-stream)",
            f"    Sub-stream x visores         : {self.sub_total_mbps:7.2f} Mbps",
            f"    Requerido                    : {self.requerido_cuadricula_mbps:7.2f} Mbps"
            f"   -> {e1}",
            "",
            "  Escenario 2 - un visor abre UNA camara"
            + ("  (sobre PRINCIPAL: la camara solo publica dos flujos)"
               if self.apertura_usa_principal else "  (sobre flujo medio)"),
            f"    Camara del peor salto        : {self.camara_de_apertura}",
            f"    Coste del salto              : {self.salto_apertura_mbps:7.2f} Mbps",
            f"    Requerido                    : {self.requerido_apertura_mbps:7.2f} Mbps"
            f"   -> {e2}",
            "",
            "  Escenario 3 - apertura sobre stream PRINCIPAL (excepcion bajo demanda)",
            f"    Camara del peor salto        : {self.camara_del_salto_principal}",
            f"    Requerido                    : {self.requerido_principal_mbps:7.2f} Mbps"
            f"   -> {e3}",
            "",
        ]
        if not self.cabe_principal:
            lineas += [
                "    Es una excepcion, no un defecto: el principal se pide a mano para revisar algo",
                "    concreto y va lento. Se explica al cliente en el diseno para que no lo",
                "    interprete como averia. NO se resuelve transcodificando (ADR-012).",
                "",
            ]
        if self.camaras_de_dos_flujos:
            lineas += [
                "  AVISO: camaras que solo publican DOS flujos, sin intermedio util:",
                "         " + ", ".join(self.camaras_de_dos_flujos),
                "         Abrirlas en remoto sirve el principal. Es la penalizacion real de esos",
                "         modelos y por eso el escenario 2 rechaza con ellas.",
                "",
            ]
        if self.hay_datos_de_catalogo:
            lineas += [
                "  AVISO: hay bitrates tomados del catalogo, no medidos en este sitio.",
                "         Confirmarlos con el firmware real de la camara instalada (M-13, M-14).",
                "",
            ]
        lineas.append("  Por camara:")
        for d in self.detalle:
            medio = f"{d['medio_mbps']:5.2f}" if d["medio_mbps"] is not None else "   - "
            lineas.append(
                f"    {d['nombre']:<32} sub {d['sub_mbps']:5.2f}  medio {medio}  "
                f"principal {d['principal_mbps']:5.1f} Mbps   ({d['streams']} flujos)"
            )
        return "\n".join(lineas)


def calcular(
    camaras: list[CamaraAB],
    visores_concurrentes: int,
    subida_disponible_mbps: float,
    margen_hogar_mbps: float = MARGEN_HOGAR_MBPS,
) -> ResultadoAnchoBanda:
    """Evalua los tres escenarios contra la subida realmente disponible."""
    if visores_concurrentes < 0:
        raise ValueError("El numero de visores concurrentes no puede ser negativo.")
    if subida_disponible_mbps <= 0:
        raise ValueError(
            "La subida disponible debe ser mayor que cero. Se mide en el relevamiento; no se toma "
            "la velocidad anunciada del plan."
        )

    # Escenario 1. Todos los visores en cuadricula: todos los sub-streams a la vez.
    sub_total = sum(c.sub_mbps for c in camaras) * visores_concurrentes
    requerido_cuadricula = sub_total + margen_hogar_mbps

    # Escenario 2. Uno de esos visores abre una camara. Peor caso del inventario: no se sabe cual.
    if camaras and visores_concurrentes > 0:
        peor = max(camaras, key=lambda c: c.salto_de_apertura_mbps)
        salto_apertura = peor.salto_de_apertura_mbps
        nombre_apertura = peor.nombre
        usa_principal = not peor.tiene_flujo_medio
    else:
        salto_apertura, nombre_apertura, usa_principal = 0.0, "-", False
    requerido_apertura = requerido_cuadricula + salto_apertura

    # Escenario 3. La misma apertura pero sobre el principal. Excepcion bajo demanda.
    if camaras and visores_concurrentes > 0:
        peor_p = max(camaras, key=lambda c: c.salto_a_principal_mbps)
        salto_principal = peor_p.salto_a_principal_mbps
        nombre_principal = peor_p.nombre
    else:
        salto_principal, nombre_principal = 0.0, "-"
    requerido_principal = requerido_cuadricula + salto_principal

    cumple_cuadricula = subida_disponible_mbps >= requerido_cuadricula
    cumple_apertura = subida_disponible_mbps >= requerido_apertura

    return ResultadoAnchoBanda(
        sub_total_mbps=sub_total,
        requerido_cuadricula_mbps=requerido_cuadricula,
        cumple_cuadricula=cumple_cuadricula,
        salto_apertura_mbps=salto_apertura,
        camara_de_apertura=nombre_apertura,
        apertura_usa_principal=usa_principal,
        requerido_apertura_mbps=requerido_apertura,
        cumple_apertura=cumple_apertura,
        salto_principal_mbps=salto_principal,
        camara_del_salto_principal=nombre_principal,
        requerido_principal_mbps=requerido_principal,
        cabe_principal=subida_disponible_mbps >= requerido_principal,
        margen_hogar_mbps=margen_hogar_mbps,
        subida_disponible_mbps=subida_disponible_mbps,
        visores_concurrentes=visores_concurrentes,
        # Los escenarios 1 y 2 son vinculantes. El 3 advierte y no rechaza.
        cumple=cumple_cuadricula and cumple_apertura,
        hay_datos_de_catalogo=any(
            c.origen_sub == "catalogo" or c.origen_medio == "catalogo" for c in camaras
        ),
        camaras_de_dos_flujos=[c.nombre for c in camaras if not c.tiene_flujo_medio],
        detalle=[
            {
                "nombre": c.nombre,
                "sub_mbps": c.sub_mbps,
                "medio_mbps": c.medio_mbps if c.tiene_flujo_medio else None,
                "principal_mbps": c.principal_mbps,
                "streams": c.streams_soportados,
            }
            for c in camaras
        ],
    )


def desde_cliente(cliente: dict, catalogo_dispositivos: list[dict] | None = None) -> ResultadoAnchoBanda:
    """Calcula a partir de un archivo de cliente, resolviendo los flujos contra el catalogo."""
    if catalogo_dispositivos is None:
        from pathlib import Path

        import yaml

        raiz = Path(__file__).resolve().parent.parent.parent
        catalogo_dispositivos = []
        for ruta in sorted((raiz / "datos-maestros" / "dispositivos").glob("*.yaml")):
            catalogo_dispositivos.extend(yaml.safe_load(ruta.read_text(encoding="utf-8")) or [])

    por_id = {d["id"]: d for d in (catalogo_dispositivos or [])}
    camaras = [
        resolver_camara(cam, por_id.get(cam.get("id_catalogo")))
        for cam in cliente.get("camaras", [])
    ]

    red = cliente.get("red", {})
    # `subida_medida_mbps` y no `subida_mbps`: el numero tiene que venir de una medicion con fecha y
    # metodo, no del folleto del proveedor. El validador rechaza el campo antiguo.
    return calcular(
        camaras,
        visores_concurrentes=cliente.get("visores_concurrentes", 1),
        subida_disponible_mbps=red.get("subida_medida_mbps", red.get("subida_mbps", 0)),
        margen_hogar_mbps=red.get("margen_hogar_mbps", MARGEN_HOGAR_MBPS),
    )


if __name__ == "__main__":
    import argparse
    import sys

    import yaml

    ap = argparse.ArgumentParser(description="Calcula el ancho de banda de subida de un cliente.")
    ap.add_argument("cliente", help="Ruta del archivo de variables del cliente.")
    args = ap.parse_args()

    with open(args.cliente, encoding="utf-8") as fh:
        datos = yaml.safe_load(fh)

    resultado = desde_cliente(datos)
    print(resultado.resumen())
    sys.exit(0 if resultado.cumple else 1)
