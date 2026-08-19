#!/usr/bin/env python3
"""Calculadora de presupuesto PoE.

Regla de dimensionado (cap. 8.2.2 del plan de negocio): se suma el consumo en PEOR CASO de todos los
dispositivos alimentados -incluidos el infrarrojo nocturno y el calefactor de invierno- y se
especifica un switch con al menos un **40 % de holgura**.

Por que la holgura no es opcional: un presupuesto PoE ajustado produce caidas intermitentes de camara
por la noche. Son extremadamente dificiles de diagnosticar despues, porque solo aparecen con frio y
oscuridad, es decir, exactamente cuando nadie esta mirando y cuando el cliente mas confia en el
sistema. El coste de sobredimensionar el switch es una fraccion del coste de una visita de
diagnostico en enero.

Sin dependencias externas. Pruebas en `test_calc_poe.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

HOLGURA_MINIMA = 0.40

# Consumo tipico en peor caso, en vatios, por tipo de dispositivo (cap. 8.2.2).
# Son valores de PARTIDA para el dimensionado. El consumo real del SKU concreto se verifica contra
# la ficha tecnica y sustituye a estos en cuanto se conoce (ADR-001).
CONSUMO_TIPICO_W = {
    "camara_2k": 8.0,                    # domo o bala fija 2K, clase 802.3af
    "camara_4k_ir": 13.0,                # 4K con iluminacion infrarroja nocturna, clase 802.3at
    "camara_4k_ir_calefactor": 25.0,     # con calefactor para operacion invernal, 802.3at o 802.3bt
    "punto_acceso": 20.0,                # clase 802.3at
    "coordinador_zigbee": 4.0,           # clase 802.3af
    "panel_tactil": 15.0,                # clase 802.3at
}

CLASE_POE = {
    "camara_2k": "802.3af",
    "camara_4k_ir": "802.3at",
    "camara_4k_ir_calefactor": "802.3at/bt",
    "punto_acceso": "802.3at",
    "coordinador_zigbee": "802.3af",
    "panel_tactil": "802.3at",
}


@dataclass
class DispositivoPoE:
    nombre: str
    tipo: str
    consumo_w: float | None = None
    """Consumo verificado del SKU concreto. Si es None se usa el tipico del tipo.

    Cuando esto deja de ser None para todo el inventario, el calculo pasa de estimacion a dato, y
    conviene anotarlo asi en la propuesta.
    """

    def peor_caso_w(self) -> float:
        if self.consumo_w is not None:
            return self.consumo_w
        if self.tipo not in CONSUMO_TIPICO_W:
            raise ValueError(
                f"{self.nombre}: tipo PoE desconocido '{self.tipo}'. "
                f"Tipos validos: {', '.join(sorted(CONSUMO_TIPICO_W))}"
            )
        return CONSUMO_TIPICO_W[self.tipo]

    def es_estimado(self) -> bool:
        return self.consumo_w is None


@dataclass
class ResultadoPoE:
    peor_caso_w: float
    requerido_w: float
    presupuesto_switch_w: float
    holgura_real: float
    cumple: bool
    puertos_usados: int
    hay_estimaciones: bool
    detalle: list[dict] = field(default_factory=list)

    def resumen(self) -> str:
        estado = "CUMPLE" if self.cumple else "NO CUMPLE"
        lineas = [
            "CALCULO DE PRESUPUESTO PoE",
            f"  Consumo en peor caso      : {self.peor_caso_w:8.1f} W  ({self.puertos_usados} puertos)",
            f"  {('Requerido con ' + format(HOLGURA_MINIMA, '.0%') + ' holgura'):<26}: {self.requerido_w:8.1f} W",
            f"  Presupuesto del switch    : {self.presupuesto_switch_w:8.1f} W",
            f"  Holgura real              : {self.holgura_real:8.1%}   -> {estado}",
        ]
        if self.hay_estimaciones:
            lineas.append(
                "  AVISO: hay consumos estimados por tipo. Sustituir por el dato de ficha tecnica"
            )
            lineas.append("         del SKU antes de comprometer el switch (ADR-001).")
        lineas.append("")
        lineas.append("  Por dispositivo:")
        for d in self.detalle:
            marca = " (estimado)" if d["estimado"] else ""
            lineas.append(
                f"    {d['nombre']:<32} {d['tipo']:<26} {d['w']:5.1f} W  {d['clase']}{marca}"
            )
        return "\n".join(lineas)


def calcular(
    dispositivos: list[DispositivoPoE],
    presupuesto_switch_w: float,
    holgura_minima: float = HOLGURA_MINIMA,
) -> ResultadoPoE:
    """Comprueba si el switch especificado sostiene la carga con la holgura exigida."""
    if presupuesto_switch_w <= 0:
        raise ValueError("El presupuesto PoE del switch debe ser mayor que cero.")

    detalle = []
    peor_caso = 0.0
    estimados = False
    for d in dispositivos:
        w = d.peor_caso_w()
        peor_caso += w
        if d.es_estimado():
            estimados = True
        detalle.append(
            {
                "nombre": d.nombre,
                "tipo": d.tipo,
                "w": w,
                "clase": CLASE_POE.get(d.tipo, "por verificar"),
                "estimado": d.es_estimado(),
            }
        )

    requerido = peor_caso * (1 + holgura_minima)
    # Holgura real: cuanto sobra sobre la carga, no sobre el requerido.
    holgura_real = (presupuesto_switch_w - peor_caso) / peor_caso if peor_caso else float("inf")

    return ResultadoPoE(
        peor_caso_w=peor_caso,
        requerido_w=requerido,
        presupuesto_switch_w=presupuesto_switch_w,
        holgura_real=holgura_real,
        cumple=presupuesto_switch_w >= requerido,
        puertos_usados=len(dispositivos),
        hay_estimaciones=estimados,
        detalle=detalle,
    )


def desde_cliente(cliente: dict) -> ResultadoPoE:
    """Calcula a partir de un archivo de cliente ya cargado.

    Toma las camaras del inventario de camaras y el resto de dispositivos PoE de `poe.otros`.
    """
    dispositivos: list[DispositivoPoE] = []

    for cam in cliente.get("camaras", []):
        dispositivos.append(
            DispositivoPoE(
                nombre=cam["nombre"],
                tipo=cam.get("tipo_poe", "camara_4k_ir"),
                consumo_w=cam.get("consumo_w"),
            )
        )

    for otro in cliente.get("poe", {}).get("otros", []):
        dispositivos.append(
            DispositivoPoE(
                nombre=otro["nombre"],
                tipo=otro["tipo"],
                consumo_w=otro.get("consumo_w"),
            )
        )

    return calcular(
        dispositivos,
        presupuesto_switch_w=cliente.get("poe", {}).get("presupuesto_switch_w", 0),
    )


if __name__ == "__main__":
    import argparse
    import sys

    import yaml

    ap = argparse.ArgumentParser(description="Calcula el presupuesto PoE de un cliente.")
    ap.add_argument("cliente", help="Ruta del archivo de variables del cliente.")
    args = ap.parse_args()

    with open(args.cliente, encoding="utf-8") as fh:
        datos = yaml.safe_load(fh)

    resultado = desde_cliente(datos)
    print(resultado.resumen())
    sys.exit(0 if resultado.cumple else 1)
