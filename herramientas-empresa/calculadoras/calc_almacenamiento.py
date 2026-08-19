#!/usr/bin/env python3
"""Calculadora de almacenamiento de video.

Este calculo se PUBLICA EN CADA PROPUESTA. Los competidores citan periodos de retencion sin
haberlo hecho; adjuntarlo es una ventaja comercial directa y evita la conversacion incomoda del mes
tres, cuando el cliente descubre que sus catorce dias son en realidad cinco.

Formula (cap. 6.12 del plan de negocio):

    TB = (Mbps / 8) * 86400 * camaras * dias / 1e6

Regla practica de contraste: una camara a 8 Mbps consume unos 86 GB al dia.

Sin dependencias externas. Pruebas en `test_calc_almacenamiento.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEGUNDOS_POR_DIA = 86_400


def tb_por_camara_dia(bitrate_mbps: float) -> float:
    """Terabytes que consume UNA camara en UN dia de grabacion continua."""
    if bitrate_mbps < 0:
        raise ValueError("El bitrate no puede ser negativo.")
    return (bitrate_mbps / 8) * SEGUNDOS_POR_DIA / 1e6


def tb_continua(bitrate_mbps: float, camaras: int, dias: float) -> float:
    """Almacenamiento de grabacion continua, en TB.

    Es la formula del plan de negocio aplicada tal cual, con todas las camaras al mismo bitrate.
    Para camaras con bitrate distinto, usar `calcular()`.
    """
    if camaras < 0 or dias < 0:
        raise ValueError("El numero de camaras y los dias no pueden ser negativos.")
    return tb_por_camara_dia(bitrate_mbps) * camaras * dias


@dataclass
class Camara:
    """Una camara del diseno, con sus dos flujos.

    El stream principal es el que se graba. El sub-stream solo alimenta la deteccion y no consume
    almacenamiento apreciable, pero si consume ancho de banda de subida cuando alguien mira en
    remoto: ver calc_ancho_banda.py.
    """

    nombre: str
    bitrate_principal_mbps: float
    bitrate_substream_mbps: float = 1.0
    fraccion_eventos: float = 0.10
    """Fraccion del tiempo con evento de persona o vehiculo.

    0,10 significa que el 10 % del dia contiene actividad que se retiene en la ventana larga. Es el
    parametro que hay que ajustar por sitio: una camara que mira a la via publica puede estar por
    encima de 0,30 y disparar el almacenamiento de eventos. Se afina tras la primera semana de
    grabacion real, y el as-built recoge el valor usado.
    """


@dataclass
class ResultadoAlmacenamiento:
    tb_continua: float
    tb_eventos: float
    tb_total: float
    tb_con_margen: float
    margen_aplicado: float
    gb_por_dia: float
    detalle_por_camara: list[dict] = field(default_factory=list)

    def resumen(self) -> str:
        lineas = [
            "CALCULO DE ALMACENAMIENTO",
            f"  Grabacion continua        : {self.tb_continua:8.2f} TB",
            f"  Eventos (ventana larga)   : {self.tb_eventos:8.2f} TB",
            f"  Total                     : {self.tb_total:8.2f} TB",
            f"  {('Con margen del ' + format(self.margen_aplicado, '.0%')):<26}: {self.tb_con_margen:8.2f} TB",
            f"  Escritura diaria          : {self.gb_por_dia:8.1f} GB/dia",
            "",
            "  Por camara:",
        ]
        for d in self.detalle_por_camara:
            lineas.append(
                f"    {d['nombre']:<32} {d['bitrate_mbps']:5.1f} Mbps"
                f"  continua {d['tb_continua']:6.2f} TB"
                f"  eventos {d['tb_eventos']:6.2f} TB"
            )
        return "\n".join(lineas)


def calcular(
    camaras: list[Camara],
    dias_continua: float,
    dias_eventos: float,
    margen: float = 0.15,
) -> ResultadoAlmacenamiento:
    """Almacenamiento requerido con RETENCION HIBRIDA.

    La retencion hibrida es la oferta por defecto: ventana continua corta mas ventana de eventos
    larga. Reduce el total entre la mitad y dos tercios conservando exactamente lo que el cliente
    busca despues, que nunca es "el martes a las cuatro de la madrugada" sino "quien se acerco a la
    puerta".

    `margen` cubre el sistema de archivos, los metadatos y la variacion de bitrate del codec, que
    en escenas con movimiento se dispara por encima del nominal.
    """
    if dias_continua < 0 or dias_eventos < 0:
        raise ValueError("Los dias de retencion no pueden ser negativos.")
    if dias_eventos < dias_continua:
        raise ValueError(
            "La ventana de eventos no puede ser mas corta que la continua: el material de evento "
            "quedaria borrado por la purga de la grabacion continua."
        )

    total_continua = 0.0
    total_eventos = 0.0
    detalle = []

    for cam in camaras:
        if not 0.0 <= cam.fraccion_eventos <= 1.0:
            raise ValueError(f"{cam.nombre}: fraccion_eventos debe estar entre 0 y 1.")
        por_dia = tb_por_camara_dia(cam.bitrate_principal_mbps)
        continua = por_dia * dias_continua
        # Los eventos solo ocupan el tramo que EXCEDE la ventana continua: lo anterior ya esta
        # contado en la grabacion continua. Contarlo dos veces infla el presupuesto y encarece la
        # propuesta sin motivo.
        eventos = por_dia * cam.fraccion_eventos * max(0.0, dias_eventos - dias_continua)
        total_continua += continua
        total_eventos += eventos
        detalle.append(
            {
                "nombre": cam.nombre,
                "bitrate_mbps": cam.bitrate_principal_mbps,
                "tb_continua": continua,
                "tb_eventos": eventos,
            }
        )

    total = total_continua + total_eventos
    gb_dia = sum(tb_por_camara_dia(c.bitrate_principal_mbps) for c in camaras) * 1000

    return ResultadoAlmacenamiento(
        tb_continua=total_continua,
        tb_eventos=total_eventos,
        tb_total=total,
        tb_con_margen=total * (1 + margen),
        margen_aplicado=margen,
        gb_por_dia=gb_dia,
        detalle_por_camara=detalle,
    )


def desde_cliente(cliente: dict) -> ResultadoAlmacenamiento:
    """Calcula a partir de un archivo de cliente ya cargado."""
    camaras = [
        Camara(
            nombre=c["nombre"],
            bitrate_principal_mbps=c["bitrate_principal_mbps"],
            bitrate_substream_mbps=c.get("bitrate_substream_mbps", 1.0),
            fraccion_eventos=c.get("fraccion_eventos", 0.10),
        )
        for c in cliente.get("camaras", [])
    ]
    ret = cliente.get("retencion", {})
    return calcular(
        camaras,
        dias_continua=ret.get("continua_dias", 7),
        dias_eventos=ret.get("eventos_dias", 30),
        margen=ret.get("margen", 0.15),
    )


if __name__ == "__main__":
    import argparse
    import sys

    import yaml

    ap = argparse.ArgumentParser(description="Calcula el almacenamiento de video de un cliente.")
    ap.add_argument("cliente", help="Ruta del archivo de variables del cliente.")
    args = ap.parse_args()

    with open(args.cliente, encoding="utf-8") as fh:
        datos = yaml.safe_load(fh)

    print(desde_cliente(datos).resumen())
    sys.exit(0)
