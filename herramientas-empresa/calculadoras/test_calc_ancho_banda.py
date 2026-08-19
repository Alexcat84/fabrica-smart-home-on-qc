"""Pruebas de la calculadora de ancho de banda de subida.

Lo que protegen: que el diseno no prometa visionado remoto que el enlace del sitio no puede
sostener. Un visor remoto tirando de flujos principales satura casi cualquier subida residencial y
el cliente lo percibe como averia del sistema, no como limite de su plan de internet.

Se evaluan dos escenarios y los dos tienen que caber. Es el resultado de la fila M-12, cerrada;
la medicion pendiente por modelo es M-13.

  1. Vista general  - todos los visores concurrentes sobre sub-stream.
  2. Escalamiento   - uno de esos visores abre UNA camara en stream principal.

El sub-stream se lee del registro del dispositivo, no de una constante. Si nadie lo ha medido, el
calculo falla en lugar de suponerlo.
"""

import unittest

from calc_ancho_banda import (
    MARGEN_HOGAR_MBPS,
    CamaraAB,
    SubstreamSinMedir,
    calcular,
    desde_cliente,
    resolver_substream,
)


def camara(nombre="cam", principal=8.0, sub=0.5, origen="cliente") -> CamaraAB:
    return CamaraAB(nombre, principal, sub, origen)


# =================================================================================================
# Resolucion del sub-stream: catalogo, cliente, o error
# =================================================================================================

class ResolucionDelSubstream(unittest.TestCase):
    def test_el_cliente_manda_sobre_el_catalogo(self):
        """El dato del sitio se midio con el firmware que tiene esa camara concreta."""
        valor, origen = resolver_substream(
            {"nombre": "cam", "bitrate_substream_mbps": 0.4},
            {"substream_bitrate_mbps": 1.0},
        )
        self.assertEqual(valor, 0.4)
        self.assertEqual(origen, "cliente")

    def test_cae_al_catalogo_cuando_el_cliente_no_lo_declara(self):
        valor, origen = resolver_substream(
            {"nombre": "cam"},
            {"substream_bitrate_mbps": 0.6},
        )
        self.assertEqual(valor, 0.6)
        self.assertEqual(origen, "catalogo")

    def test_sin_medicion_falla_en_lugar_de_suponer(self):
        """El fallo que esta prueba fija: antes existia una constante de 1.0 Mbps por defecto.

        Un valor por defecto convierte una promesa comercial -dos visores concurrentes- en una
        suposicion que nadie ha comprobado. ADR-001.
        """
        with self.assertRaises(SubstreamSinMedir) as ctx:
            resolver_substream({"nombre": "cam", "id_catalogo": "reolink-poe-camara"}, {})
        self.assertIn("sub-stream", str(ctx.exception))
        self.assertIn("M-13", str(ctx.exception))

    def test_sin_registro_de_catalogo_tambien_falla(self):
        with self.assertRaises(SubstreamSinMedir):
            resolver_substream({"nombre": "cam"}, None)

    def test_un_cero_declarado_es_un_valor_valido_no_una_ausencia(self):
        valor, origen = resolver_substream({"nombre": "cam", "bitrate_substream_mbps": 0.0}, None)
        self.assertEqual(valor, 0.0)
        self.assertEqual(origen, "cliente")


# =================================================================================================
# Escenario 1: vista general
# =================================================================================================

class EscenarioVistaGeneral(unittest.TestCase):
    def test_todos_los_substreams_por_todos_los_visores(self):
        r = calcular([camara(sub=0.5) for _ in range(5)], 2, subida_disponible_mbps=25.0)
        self.assertEqual(r.substream_total_mbps, 5.0)
        self.assertEqual(r.requerido_general_mbps, 10.0)
        self.assertTrue(r.cumple_general)

    def test_paquete_s_un_visor(self):
        r = calcular([camara(principal=4.0, sub=0.5) for _ in range(3)], 1,
                     subida_disponible_mbps=5.0, margen_hogar_mbps=2.0)
        self.assertAlmostEqual(r.substream_total_mbps, 1.5, places=2)
        self.assertTrue(r.cumple_general)

    def test_sin_margen_el_calculo_miente(self):
        """Sin margen, el sistema ocupa toda la subida y la videollamada del cliente se cae."""
        justo = calcular([camara(sub=1.0) for _ in range(5)], 2,
                         subida_disponible_mbps=10.0, margen_hogar_mbps=0.0)
        real = calcular([camara(sub=1.0) for _ in range(5)], 2,
                        subida_disponible_mbps=10.0, margen_hogar_mbps=5.0)
        self.assertTrue(justo.cumple_general)
        self.assertFalse(real.cumple_general)


# =================================================================================================
# Escenario 2: escalamiento a stream principal
# =================================================================================================

class EscenarioEscalamiento(unittest.TestCase):
    def test_el_minimo_publicado_del_paquete_m_no_sobrevive_al_escalamiento(self):
        """HALLAZGO CENTRAL DE M-12, y la razon de que exista el segundo escenario.

        El minimo publicado para M son 10 Mbps de subida con dos flujos remotos simultaneos. Con
        cinco camaras a 0,5 Mbps de sub-stream, la vista general pide exactamente 10 Mbps y encaja
        al milimetro. Pero en cuanto uno de los dos visores abre una camara 4K en stream principal
        -que es lo que cualquiera hace al ver movimiento- el salto de 7,5 Mbps lleva el total a
        17,5 y el enlace se queda corto.

        El minimo publicado solo cubre mirar, no cubre mirar de cerca.
        """
        camaras = [camara(principal=8.0, sub=0.5) for _ in range(5)]
        r = calcular(camaras, 2, subida_disponible_mbps=10.0)
        self.assertTrue(r.cumple_general, "la vista general si encaja en el minimo publicado")
        self.assertFalse(r.cumple_escalamiento, "el escalamiento no")
        self.assertEqual(r.requerido_escalamiento_mbps, 17.5)
        self.assertFalse(r.cumple, "el resultado global exige que pasen los dos escenarios")

    def test_se_toma_el_peor_salto_del_inventario(self):
        """No se sabe que camara va a tocar el visor, asi que se supone la peor."""
        camaras = [
            camara("patio", principal=4.0, sub=0.5),
            camara("frente", principal=8.0, sub=0.5),
            camara("garaje", principal=4.0, sub=0.5),
        ]
        r = calcular(camaras, 1, subida_disponible_mbps=25.0)
        self.assertEqual(r.camara_del_salto, "frente")
        self.assertEqual(r.salto_maximo_mbps, 7.5)

    def test_el_salto_descuenta_el_substream_que_deja_de_pedir(self):
        """Al escalar, ese visor deja de tirar del sub-stream de esa camara: se resta."""
        r = calcular([camara(principal=8.0, sub=2.0)], 1, subida_disponible_mbps=25.0)
        self.assertEqual(r.salto_maximo_mbps, 6.0)

    def test_con_mas_subida_los_dos_escenarios_encajan(self):
        camaras = [camara(principal=8.0, sub=0.5) for _ in range(5)]
        r = calcular(camaras, 2, subida_disponible_mbps=25.0)
        self.assertTrue(r.cumple_general)
        self.assertTrue(r.cumple_escalamiento)
        self.assertTrue(r.cumple)

    def test_sin_camaras_no_hay_salto(self):
        r = calcular([], 1, subida_disponible_mbps=5.0)
        self.assertEqual(r.salto_maximo_mbps, 0.0)
        self.assertEqual(r.camara_del_salto, "-")
        self.assertEqual(r.requerido_escalamiento_mbps, MARGEN_HOGAR_MBPS)
        self.assertTrue(r.cumple)

    def test_sin_visores_no_hay_salto(self):
        r = calcular([camara(principal=8.0, sub=0.5)], 0, subida_disponible_mbps=5.0)
        self.assertEqual(r.salto_maximo_mbps, 0.0)
        self.assertTrue(r.cumple)


# =================================================================================================
# Caso extremo, informativo
# =================================================================================================

class TodosLosStreamsPrincipales(unittest.TestCase):
    def test_cuatro_camaras_4k_no_caben_en_enlace_residencial(self):
        """El caso que el plan advierte: cuatro flujos 4K principales saturan casi cualquier subida."""
        camaras = [camara(principal=8.0, sub=1.0) for _ in range(4)]
        r = calcular(camaras, 1, subida_disponible_mbps=25.0)
        self.assertTrue(r.cumple, "los dos escenarios reales si encajan")
        self.assertFalse(r.cumple_todos_principales, "el caso extremo no, y por eso es bajo demanda")
        self.assertEqual(r.principal_total_mbps, 32.0)

    def test_con_fibra_simetrica_si_caben(self):
        camaras = [camara(principal=8.0, sub=1.0) for _ in range(4)]
        r = calcular(camaras, 1, subida_disponible_mbps=50.0)
        self.assertTrue(r.cumple_todos_principales)


# =================================================================================================
# Procedencia del dato y argumento comercial
# =================================================================================================

class ProcedenciaDelDato(unittest.TestCase):
    def test_se_avisa_cuando_el_substream_viene_del_catalogo(self):
        r = calcular([camara(origen="catalogo")], 1, subida_disponible_mbps=25.0)
        self.assertTrue(r.hay_substream_de_catalogo)
        self.assertIn("catalogo", r.resumen())

    def test_no_se_avisa_cuando_todo_se_midio_en_el_sitio(self):
        r = calcular([camara(origen="cliente")], 1, subida_disponible_mbps=25.0)
        self.assertFalse(r.hay_substream_de_catalogo)


class ArgumentoComercial(unittest.TestCase):
    def test_el_sistema_local_consume_ordenes_de_magnitud_menos(self):
        """4 camaras a 2 Mbps: la nube sube ~2.600 GB/mes; el sistema local, decenas."""
        camaras = [camara(principal=2.0, sub=1.0) for _ in range(4)]
        r = calcular(camaras, 1, subida_disponible_mbps=25.0, horas_visionado_dia=1.0)
        self.assertAlmostEqual(r.consumo_nube_equivalente_gb_mes, 2592.0, places=0)
        self.assertLess(r.consumo_reposo_gb_mes, 100)
        self.assertGreater(r.consumo_nube_equivalente_gb_mes / r.consumo_reposo_gb_mes, 20)


# =================================================================================================
# Entradas invalidas
# =================================================================================================

class EntradasInvalidas(unittest.TestCase):
    def test_subida_cero_es_error_no_resultado(self):
        with self.assertRaises(ValueError) as ctx:
            calcular([camara()], 1, subida_disponible_mbps=0)
        self.assertIn("relevamiento", str(ctx.exception))

    def test_visores_negativos(self):
        with self.assertRaises(ValueError):
            calcular([camara()], -1, subida_disponible_mbps=25.0)


# =================================================================================================
# Integracion con el archivo de cliente
# =================================================================================================

class DesdeCliente(unittest.TestCase):
    CATALOGO = [
        {"id": "camara-medida", "substream_bitrate_mbps": 0.6},
        {"id": "camara-sin-medir", "substream_bitrate_mbps": None},
    ]

    def test_lee_el_substream_del_catalogo(self):
        cliente = {
            "camaras": [
                {"nombre": "c1", "id_catalogo": "camara-medida", "bitrate_principal_mbps": 4.0}
            ],
            "visores_concurrentes": 1,
            "red": {"subida_mbps": 25.0},
        }
        r = desde_cliente(cliente, self.CATALOGO)
        self.assertEqual(r.substream_total_mbps, 0.6)
        self.assertTrue(r.hay_substream_de_catalogo)

    def test_una_camara_sin_medir_hace_fallar_el_calculo_entero(self):
        cliente = {
            "camaras": [
                {"nombre": "c1", "id_catalogo": "camara-medida", "bitrate_principal_mbps": 4.0},
                {"nombre": "c2", "id_catalogo": "camara-sin-medir", "bitrate_principal_mbps": 4.0},
            ],
            "visores_concurrentes": 1,
            "red": {"subida_mbps": 25.0},
        }
        with self.assertRaises(SubstreamSinMedir) as ctx:
            desde_cliente(cliente, self.CATALOGO)
        self.assertIn("c2", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
