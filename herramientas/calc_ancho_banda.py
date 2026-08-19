#!/usr/bin/env python3
"""Calculadora de ancho de banda de subida.

Regla (cap. 8.3 del plan de negocio): bitrate del SUB-STREAM por visores concurrentes, mas margen
para el trafico normal del hogar.

Dos cosas que hay que entender y que el cliente no sabe:

1. **La subida es la restriccion, no la bajada.** El servicio de cable canadiense es fuertemente
   asimetrico; la fibra suele ser simetrica. Se mide la subida REAL en el relevamiento, no la
   velocidad anunciada del plan.

2. **Siempre se sirve el sub-stream por defecto** en visionado remoto, y se pasa al principal solo
   bajo demanda. Un visor remoto tirando de cuatro flujos 4K principales satura casi cualquier enlace
   residencial y se percibe como una averia del sistema, no como un limite del enlace.

La ventaja estructural que conviene poner en la propuesta: en reposo, un sistema local no consume
practicamente nada de subida. Un servicio en la nube sube cada segundo de cada camara, todos los
dias. Para un hogar canadiense con plan medido, eso es un coste mensual real que ya esta pagando y
que no ve.

Sin dependencias externas. Pruebas en `test_calc_ancho_banda.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

MARGEN_HOGAR_MBPS = 5.0
"""Subida reservada al uso normal del hogar: videollamadas, respaldos, juego en linea.

No es un colchon de cortesia. Sin el, la primera videollamada de trabajo del cliente convive con el
visionado remoto y una de las dos se degrada; el cliente culpara al sistema que acaba de instalar.
"""


@dataclass
class ResultadoAnchoBanda:
    substream_total_mbps: float
    margen_hogar_mbps: float
    requerido_mbps: float
    subida_disponible_mbps: float
    cumple: bool
    visores_concurrentes: int
    principal_total_mbps: float
    cumple_principal: bool
    consumo_reposo_gb_mes: float
    consumo_nube_equivalente_gb_mes: float

    def resumen(self) -> str:
        estado = "CUMPLE" if self.cumple else "NO CUMPLE"
        estado_principal = "si" if self.cumple_principal else "no"
        return "\n".join(
            [
                "CALCULO DE ANCHO DE BANDA DE SUBIDA",
                f"  Visores concurrentes previstos : {self.visores_concurrentes}",
                f"  Sub-stream x visores           : {self.substream_total_mbps:7.2f} Mbps",
                f"  Margen para el hogar           : {self.margen_hogar_mbps:7.2f} Mbps",
                f"  Requerido                      : {self.requerido_mbps:7.2f} Mbps",
                f"  Subida disponible (medida)     : {self.subida_disponible_mbps:7.2f} Mbps"
                f"   -> {estado}",
                "",
                f"  Si un visor pide el stream PRINCIPAL de todas las camaras: "
                f"{self.principal_total_mbps:.1f} Mbps (soportado: {estado_principal})",
                "",
                "  Argumento para la propuesta:",
                f"    Sistema local, en reposo         : ~{self.consumo_reposo_gb_mes:.0f} GB/mes de subida",
                f"    Servicio en la nube equivalente  : ~{self.consumo_nube_equivalente_gb_mes:.0f} GB/mes de subida",
            ]
        )


def calcular(
    bitrates_substream_mbps: list[float],
    bitrates_principal_mbps: list[float],
    visores_concurrentes: int,
    subida_disponible_mbps: float,
    margen_hogar_mbps: float = MARGEN_HOGAR_MBPS,
    horas_visionado_dia: float = 1.0,
) -> ResultadoAnchoBanda:
    """Comprueba si la subida del sitio sostiene el visionado remoto previsto."""
    if visores_concurrentes < 0:
        raise ValueError("El numero de visores concurrentes no puede ser negativo.")
    if subida_disponible_mbps <= 0:
        raise ValueError(
            "La subida disponible debe ser mayor que cero. Se mide en el relevamiento; no se toma "
            "la velocidad anunciada del plan."
        )

    # Un visor abre la vista general: todos los sub-streams a la vez. Es el caso real, no el
    # optimista de "una camara cada vez".
    substream_total = sum(bitrates_substream_mbps) * visores_concurrentes
    requerido = substream_total + margen_hogar_mbps

    principal_total = sum(bitrates_principal_mbps)

    # Consumo mensual, para el argumento comercial.
    reposo_gb_mes = substream_total / 8 * 3600 * horas_visionado_dia * 30 / 1000
    nube_gb_mes = sum(bitrates_principal_mbps) / 8 * 86400 * 30 / 1000

    return ResultadoAnchoBanda(
        substream_total_mbps=substream_total,
        margen_hogar_mbps=margen_hogar_mbps,
        requerido_mbps=requerido,
        subida_disponible_mbps=subida_disponible_mbps,
        cumple=subida_disponible_mbps >= requerido,
        visores_concurrentes=visores_concurrentes,
        principal_total_mbps=principal_total,
        cumple_principal=subida_disponible_mbps >= principal_total + margen_hogar_mbps,
        consumo_reposo_gb_mes=reposo_gb_mes,
        consumo_nube_equivalente_gb_mes=nube_gb_mes,
    )


def desde_cliente(cliente: dict) -> ResultadoAnchoBanda:
    """Calcula a partir de un archivo de cliente ya cargado."""
    camaras = cliente.get("camaras", [])
    red = cliente.get("red", {})
    return calcular(
        bitrates_substream_mbps=[c.get("bitrate_substream_mbps", 1.0) for c in camaras],
        bitrates_principal_mbps=[c["bitrate_principal_mbps"] for c in camaras],
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
