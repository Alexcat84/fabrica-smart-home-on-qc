#!/usr/bin/env python3
"""Calculadora de ancho de banda de subida.

Regla (cap. 8.3 del plan de negocio): bitrate del SUB-STREAM por visores concurrentes, mas margen
para el trafico normal del hogar.

Dos cosas que hay que entender y que el cliente no sabe:

1. **La subida es la restriccion, no la bajada.** El servicio de cable canadiense es fuertemente
   asimetrico; la fibra suele ser simetrica. Se mide la subida REAL en el relevamiento, no la
   velocidad anunciada del plan.

2. **Siempre se sirve el sub-stream por defecto** en visionado remoto, y se pasa al principal solo
   bajo demanda. Un visor remoto tirando de flujos principales satura casi cualquier subida
   residencial y se percibe como una averia del sistema, no como un limite del enlace.

EL SUB-STREAM ES UN PARAMETRO DE DISENO, NO UNA CONSTANTE. Es el hallazgo de la fila M-12, ya
cerrada; la medicion pendiente por modelo y firmware es la fila M-13 de docs/POR-VERIFICAR.md.
Este modulo lo lee del registro del dispositivo en `datos-maestros/dispositivos/`
(`substream_bitrate_mbps`), o del archivo de cliente cuando alli hay una medicion del sitio, que
manda sobre el catalogo. Si no hay ninguno de los dos, **no se inventa un valor**: se levanta
`SubstreamSinMedir` y el validador rechaza el cliente. Prometer dos visores concurrentes sobre un
numero que nadie ha medido es exactamente el tipo de dato inventado que prohibe ADR-001.

Se evaluan DOS escenarios y **los dos** tienen que caber en la subida declarada:

  1. Vista general      - todos los visores concurrentes sobre sub-stream.
  2. Escalamiento       - los mismos visores en vista general, y uno de ellos abre UNA camara en
                          stream principal. Es lo que la gente hace en cuanto ve algo.

La ventaja estructural que conviene poner en la propuesta: en reposo, un sistema local no consume
practicamente nada de subida. Un servicio en la nube sube cada segundo de cada camara, todos los
dias. Para un hogar canadiense con plan medido, eso es un coste mensual real que ya esta pagando y
que no ve.

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
    """No hay bitrate de sub-stream ni en el catalogo ni en el archivo de cliente.

    No se sustituye por un valor por defecto a proposito. El sub-stream determina si el minimo de
    subida del paquete se sostiene con los visores prometidos; un valor inventado convierte una
    promesa comercial en una suposicion.
    """


@dataclass
class CamaraAB:
    """Una camara, con su sub-stream ya resuelto y la procedencia del dato."""

    nombre: str
    bitrate_principal_mbps: float
    substream_mbps: float
    origen_substream: str
    """`cliente` (medido en el sitio), `catalogo` (medido en banco) o `desconocido`."""

    @property
    def salto_a_principal_mbps(self) -> float:
        """Coste adicional de que un visor escale ESTA camara al stream principal."""
        return max(0.0, self.bitrate_principal_mbps - self.substream_mbps)


def resolver_substream(camara_cliente: dict, registro_catalogo: dict | None) -> tuple[float, str]:
    """Devuelve (bitrate del sub-stream, origen del dato).

    Prioridad, y el orden importa:

    1. **El archivo de cliente**, cuando declara `bitrate_substream_mbps`. Es una medicion del sitio
       concreto, con el firmware que tiene esa camara: manda sobre cualquier valor general.
    2. **El catalogo**, `substream_bitrate_mbps` de la familia, medido en el banco de la empresa.
    3. Nada. Se levanta `SubstreamSinMedir`.
    """
    del_cliente = camara_cliente.get("bitrate_substream_mbps")
    if del_cliente is not None:
        return float(del_cliente), "cliente"

    if registro_catalogo:
        del_catalogo = registro_catalogo.get("substream_bitrate_mbps")
        if del_catalogo is not None:
            return float(del_catalogo), "catalogo"

    raise SubstreamSinMedir(
        f"La camara '{camara_cliente.get('nombre', '(sin nombre)')}' no tiene bitrate de sub-stream "
        f"ni en el archivo de cliente (`bitrate_substream_mbps`) ni en el catalogo "
        f"(`substream_bitrate_mbps` de '{camara_cliente.get('id_catalogo')}'). Medirlo en banco por "
        f"modelo y firmware, o en el sitio. No se supone un valor: de el depende si el visionado "
        f"remoto concurrente que se promete cabe en la subida contratada (M-13)."
    )


@dataclass
class ResultadoAnchoBanda:
    # Escenario 1: vista general
    substream_total_mbps: float
    requerido_general_mbps: float
    cumple_general: bool

    # Escenario 2: escalamiento a principal por un visor
    salto_maximo_mbps: float
    camara_del_salto: str
    requerido_escalamiento_mbps: float
    cumple_escalamiento: bool

    # Comun
    margen_hogar_mbps: float
    subida_disponible_mbps: float
    visores_concurrentes: int
    cumple: bool

    # Caso extremo, informativo
    principal_total_mbps: float
    cumple_todos_principales: bool

    # Argumento comercial
    consumo_reposo_gb_mes: float
    consumo_nube_equivalente_gb_mes: float

    hay_substream_de_catalogo: bool
    detalle: list[dict] = field(default_factory=list)

    def resumen(self) -> str:
        e1 = "CUMPLE" if self.cumple_general else "NO CUMPLE"
        e2 = "CUMPLE" if self.cumple_escalamiento else "NO CUMPLE"
        lineas = [
            "CALCULO DE ANCHO DE BANDA DE SUBIDA",
            f"  Visores concurrentes previstos : {self.visores_concurrentes}",
            f"  Subida disponible (medida)     : {self.subida_disponible_mbps:7.2f} Mbps",
            f"  Margen para el hogar           : {self.margen_hogar_mbps:7.2f} Mbps",
            "",
            "  Escenario 1 - vista general (todos los visores sobre sub-stream)",
            f"    Sub-stream x visores         : {self.substream_total_mbps:7.2f} Mbps",
            f"    Requerido                    : {self.requerido_general_mbps:7.2f} Mbps"
            f"   -> {e1}",
            "",
            "  Escenario 2 - un visor escala una camara al stream principal",
            f"    Camara del peor salto        : {self.camara_del_salto}",
            f"    Coste del salto              : {self.salto_maximo_mbps:7.2f} Mbps",
            f"    Requerido                    : {self.requerido_escalamiento_mbps:7.2f} Mbps"
            f"   -> {e2}",
            "",
        ]
        if self.hay_substream_de_catalogo:
            lineas.append(
                "  AVISO: hay sub-streams tomados del catalogo, no medidos en este sitio."
            )
            lineas.append(
                "         Confirmarlos con el firmware real de la camara instalada (M-13)."
            )
            lineas.append("")
        lineas += [
            f"  Caso extremo, informativo: un visor con TODOS los streams principales pediria "
            f"{self.principal_total_mbps:.1f} Mbps "
            f"(soportado: {'si' if self.cumple_todos_principales else 'no'}).",
            "",
            "  Argumento para la propuesta:",
            f"    Sistema local, en reposo         : ~{self.consumo_reposo_gb_mes:.0f} GB/mes de subida",
            f"    Servicio en la nube equivalente  : ~{self.consumo_nube_equivalente_gb_mes:.0f} GB/mes de subida",
            "",
            "  Por camara:",
        ]
        for d in self.detalle:
            lineas.append(
                f"    {d['nombre']:<32} sub {d['substream_mbps']:5.2f} Mbps "
                f"({d['origen']:<9}) principal {d['principal_mbps']:5.1f} Mbps "
                f"salto {d['salto_mbps']:5.1f} Mbps"
            )
        return "\n".join(lineas)


def calcular(
    camaras: list[CamaraAB],
    visores_concurrentes: int,
    subida_disponible_mbps: float,
    margen_hogar_mbps: float = MARGEN_HOGAR_MBPS,
    horas_visionado_dia: float = 1.0,
) -> ResultadoAnchoBanda:
    """Evalua los dos escenarios contra la subida realmente disponible."""
    if visores_concurrentes < 0:
        raise ValueError("El numero de visores concurrentes no puede ser negativo.")
    if subida_disponible_mbps <= 0:
        raise ValueError(
            "La subida disponible debe ser mayor que cero. Se mide en el relevamiento; no se toma "
            "la velocidad anunciada del plan."
        )

    # Escenario 1. Un visor abre la vista general: todos los sub-streams a la vez. Es el caso real,
    # no el optimista de "una camara cada vez".
    substream_total = sum(c.substream_mbps for c in camaras) * visores_concurrentes
    requerido_general = substream_total + margen_hogar_mbps

    # Escenario 2. Uno de esos visores toca una camara y la abre en principal. Se toma el peor salto
    # del inventario, que es el unico supuesto defendible: no se sabe cual va a tocar.
    if camaras and visores_concurrentes > 0:
        peor = max(camaras, key=lambda c: c.salto_a_principal_mbps)
        salto_maximo = peor.salto_a_principal_mbps
        camara_del_salto = peor.nombre
    else:
        salto_maximo = 0.0
        camara_del_salto = "-"
    requerido_escalamiento = requerido_general + salto_maximo

    principal_total = sum(c.bitrate_principal_mbps for c in camaras)

    reposo_gb_mes = substream_total / 8 * 3600 * horas_visionado_dia * 30 / 1000
    nube_gb_mes = principal_total / 8 * 86400 * 30 / 1000

    cumple_general = subida_disponible_mbps >= requerido_general
    cumple_escalamiento = subida_disponible_mbps >= requerido_escalamiento

    return ResultadoAnchoBanda(
        substream_total_mbps=substream_total,
        requerido_general_mbps=requerido_general,
        cumple_general=cumple_general,
        salto_maximo_mbps=salto_maximo,
        camara_del_salto=camara_del_salto,
        requerido_escalamiento_mbps=requerido_escalamiento,
        cumple_escalamiento=cumple_escalamiento,
        margen_hogar_mbps=margen_hogar_mbps,
        subida_disponible_mbps=subida_disponible_mbps,
        visores_concurrentes=visores_concurrentes,
        cumple=cumple_general and cumple_escalamiento,
        principal_total_mbps=principal_total,
        cumple_todos_principales=subida_disponible_mbps >= principal_total + margen_hogar_mbps,
        consumo_reposo_gb_mes=reposo_gb_mes,
        consumo_nube_equivalente_gb_mes=nube_gb_mes,
        hay_substream_de_catalogo=any(c.origen_substream == "catalogo" for c in camaras),
        detalle=[
            {
                "nombre": c.nombre,
                "substream_mbps": c.substream_mbps,
                "origen": c.origen_substream,
                "principal_mbps": c.bitrate_principal_mbps,
                "salto_mbps": c.salto_a_principal_mbps,
            }
            for c in camaras
        ],
    )


def desde_cliente(cliente: dict, catalogo_dispositivos: list[dict] | None = None) -> ResultadoAnchoBanda:
    """Calcula a partir de un archivo de cliente, resolviendo el sub-stream contra el catalogo.

    `catalogo_dispositivos` es la lista de `datos-maestros/dispositivos/`. Si no se pasa, se carga.
    """
    if catalogo_dispositivos is None:
        from pathlib import Path

        import yaml

        raiz = Path(__file__).resolve().parent.parent.parent
        catalogo_dispositivos = []
        for ruta in sorted((raiz / "datos-maestros" / "dispositivos").glob("*.yaml")):
            catalogo_dispositivos.extend(yaml.safe_load(ruta.read_text(encoding="utf-8")) or [])

    por_id = {d["id"]: d for d in (catalogo_dispositivos or [])}

    camaras: list[CamaraAB] = []
    for cam in cliente.get("camaras", []):
        substream, origen = resolver_substream(cam, por_id.get(cam.get("id_catalogo")))
        camaras.append(
            CamaraAB(
                nombre=cam["nombre"],
                bitrate_principal_mbps=cam["bitrate_principal_mbps"],
                substream_mbps=substream,
                origen_substream=origen,
            )
        )

    red = cliente.get("red", {})
    return calcular(
        camaras,
        visores_concurrentes=cliente.get("visores_concurrentes", 1),
        subida_disponible_mbps=red.get("subida_mbps", 0),
        margen_hogar_mbps=red.get("margen_hogar_mbps", MARGEN_HOGAR_MBPS),
        horas_visionado_dia=cliente.get("horas_visionado_dia", 1.0),
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
