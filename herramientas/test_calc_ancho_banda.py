"""Pruebas de la calculadora de ancho de banda de subida.

Lo que protegen: que el diseno no prometa visionado remoto que el enlace del sitio no puede sostener.
Un visor remoto tirando de flujos principales satura casi cualquier subida residencial y el cliente
lo percibe como averia del sistema, no como limite de su plan de internet.
"""

import unittest

from calc_ancho_banda import MARGEN_HOGAR_MBPS, calcular


class MinimosDelPlanDeNegocio(unittest.TestCase):
    """Cap. 8.3.2: minimos de subida por paquete."""

    def test_paquete_s_un_visor_sobre_5_mbps(self):
        # S: 3 camaras, un sub-stream remoto a la vez, subida minima 5 Mbps.
        # Con margen de hogar de 5 Mbps el minimo publicado se queda justo: la prueba documenta
        # que el margen hay que ajustarlo a la baja en el nivel S o subir el enlace.
        r = calcular([0.5] * 3, [4.0] * 3, visores_concurrentes=1,
                     subida_disponible_mbps=5.0, margen_hogar_mbps=2.0)
        self.assertTrue(r.cumple)
        self.assertAlmostEqual(r.substream_total_mbps, 1.5, places=2)

    def test_paquete_m_el_minimo_publicado_exige_sub_streams_ajustados(self):
        """HALLAZGO REAL, no un ajuste de la prueba.

        El minimo publicado para M son 10 Mbps de subida con dos flujos remotos simultaneos. Con
        cinco camaras cuyo sub-stream vaya a 1 Mbps, dos visores piden 10 Mbps y no queda nada para
        el hogar: el minimo publicado NO se sostiene.

        Con el sub-stream dimensionado como corresponde -640x480 a 5 fps ronda 0,5 Mbps- si se
        sostiene con holgura. La consecuencia practica es que el sub-stream de cada camara es un
        parametro de diseno, no un valor por defecto que se hereda de la camara: se fija en el
        comisionamiento y se anota en el as-built. Fila abierta en docs/POR-VERIFICAR.md.
        """
        holgado = calcular([1.0] * 5, [8.0] * 5, visores_concurrentes=2, subida_disponible_mbps=10.0)
        self.assertEqual(holgado.requerido_mbps, 15.0)
        self.assertFalse(holgado.cumple)

        ajustado = calcular([0.5] * 5, [8.0] * 5, visores_concurrentes=2, subida_disponible_mbps=10.0)
        self.assertEqual(ajustado.requerido_mbps, 10.0)
        self.assertTrue(ajustado.cumple)

    def test_paquete_l_multiples_visores_sobre_25_mbps(self):
        r = calcular([1.0] * 10, [8.0] * 10, visores_concurrentes=2, subida_disponible_mbps=25.0)
        self.assertTrue(r.cumple)


class ElStreamPrincipalSatura(unittest.TestCase):
    def test_cuatro_camaras_4k_en_principal_no_caben_en_enlace_residencial(self):
        """El caso que el plan advierte: cuatro flujos 4K principales saturan casi cualquier subida."""
        r = calcular([1.0] * 4, [8.0] * 4, visores_concurrentes=1, subida_disponible_mbps=25.0)
        self.assertTrue(r.cumple, "El sub-stream si cabe")
        self.assertFalse(r.cumple_principal, "El principal no, y por eso es bajo demanda")
        self.assertEqual(r.principal_total_mbps, 32.0)

    def test_con_fibra_simetrica_si_caben(self):
        r = calcular([1.0] * 4, [8.0] * 4, visores_concurrentes=1, subida_disponible_mbps=50.0)
        self.assertTrue(r.cumple_principal)


class MargenDelHogar(unittest.TestCase):
    def test_sin_margen_el_calculo_miente(self):
        """Sin margen, el sistema ocupa toda la subida y la videollamada del cliente se cae."""
        justo = calcular([1.0] * 5, [8.0] * 5, 2, subida_disponible_mbps=10.0, margen_hogar_mbps=0.0)
        real = calcular([1.0] * 5, [8.0] * 5, 2, subida_disponible_mbps=10.0, margen_hogar_mbps=5.0)
        self.assertTrue(justo.cumple)
        self.assertFalse(real.cumple)


class ArgumentoComercial(unittest.TestCase):
    def test_el_sistema_local_consume_ordenes_de_magnitud_menos(self):
        """4 camaras a 2 Mbps: la nube sube ~2.600 GB/mes; el sistema local, decenas."""
        r = calcular([1.0] * 4, [2.0] * 4, visores_concurrentes=1,
                     subida_disponible_mbps=25.0, horas_visionado_dia=1.0)
        self.assertAlmostEqual(r.consumo_nube_equivalente_gb_mes, 2592.0, places=0)
        self.assertLess(r.consumo_reposo_gb_mes, 100)
        self.assertGreater(r.consumo_nube_equivalente_gb_mes / r.consumo_reposo_gb_mes, 20)


class EntradasInvalidas(unittest.TestCase):
    def test_subida_cero_es_error_no_resultado(self):
        with self.assertRaises(ValueError) as ctx:
            calcular([1.0], [8.0], 1, subida_disponible_mbps=0)
        self.assertIn("relevamiento", str(ctx.exception))

    def test_visores_negativos(self):
        with self.assertRaises(ValueError):
            calcular([1.0], [8.0], -1, subida_disponible_mbps=25.0)

    def test_sin_camaras_solo_queda_el_margen(self):
        r = calcular([], [], 1, subida_disponible_mbps=5.0)
        self.assertEqual(r.substream_total_mbps, 0.0)
        self.assertEqual(r.requerido_mbps, MARGEN_HOGAR_MBPS)
        self.assertTrue(r.cumple)


if __name__ == "__main__":
    unittest.main()
