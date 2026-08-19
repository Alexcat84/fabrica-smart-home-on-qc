"""Pruebas de la calculadora de almacenamiento.

Los casos estan ANCLADOS en la tabla publicada del cap. 6.12 del plan de negocio. Si una de estas
pruebas falla, o hemos roto la formula o la tabla de la propuesta comercial ha dejado de ser cierta.
Las dos cosas son graves.
"""

import unittest

from calc_almacenamiento import Camara, calcular, tb_continua, tb_por_camara_dia


class ReglaPractica(unittest.TestCase):
    def test_una_camara_8mbps_consume_unos_86gb_al_dia(self):
        # Regla practica que aparece literalmente en el plan de negocio.
        self.assertAlmostEqual(tb_por_camara_dia(8.0) * 1000, 86.4, places=1)


class TablaDelPlanDeNegocio(unittest.TestCase):
    """Tabla del cap. 6.12: grabacion continua, sin retencion hibrida."""

    def test_4_camaras_4mbps_por_dia(self):
        # "4 camaras a 4 Mbps -> 172 GB por dia"
        self.assertAlmostEqual(tb_continua(4.0, 4, 1) * 1000, 172.8, places=1)

    def test_4_camaras_4mbps_14_dias(self):
        # "aprox. 2,4 TB"
        self.assertAlmostEqual(tb_continua(4.0, 4, 14), 2.42, places=2)

    def test_4_camaras_4mbps_30_dias(self):
        # "aprox. 5,2 TB"
        self.assertAlmostEqual(tb_continua(4.0, 4, 30), 5.18, places=2)

    def test_6_camaras_8mbps_por_dia(self):
        # "516 GB por dia"
        self.assertAlmostEqual(tb_continua(8.0, 6, 1) * 1000, 518.4, places=1)

    def test_6_camaras_8mbps_14_dias(self):
        # "aprox. 7,2 TB" - este es el caso de referencia del paquete M
        self.assertAlmostEqual(tb_continua(8.0, 6, 14), 7.26, places=2)

    def test_10_camaras_8mbps_30_dias(self):
        # "aprox. 25,8 TB"
        self.assertAlmostEqual(tb_continua(8.0, 10, 30), 25.92, places=2)

    def test_16_camaras_6mbps_14_dias(self):
        # "aprox. 14,5 TB"
        self.assertAlmostEqual(tb_continua(6.0, 16, 14), 14.52, places=2)


class RetencionHibrida(unittest.TestCase):
    def setUp(self):
        self.camaras = [
            Camara(f"camara_{i}", bitrate_principal_mbps=8.0, fraccion_eventos=0.10)
            for i in range(6)
        ]

    def test_hibrida_reduce_frente_a_continua_larga(self):
        """La afirmacion comercial: la hibrida reduce entre la mitad y dos tercios."""
        continua_60 = tb_continua(8.0, 6, 60)
        hibrida = calcular(self.camaras, dias_continua=7, dias_eventos=60, margen=0.0)
        reduccion = 1 - (hibrida.tb_total / continua_60)
        self.assertGreater(reduccion, 0.50, "La hibrida deberia ahorrar mas del 50 %")
        self.assertLess(reduccion, 0.95, "Un ahorro de mas del 95 % indica un error de calculo")

    def test_los_eventos_no_se_cuentan_dos_veces(self):
        """El material de evento dentro de la ventana continua ya esta contado."""
        r = calcular(self.camaras, dias_continua=30, dias_eventos=30, margen=0.0)
        self.assertEqual(r.tb_eventos, 0.0)

    def test_el_margen_se_aplica_sobre_el_total(self):
        sin = calcular(self.camaras, 7, 60, margen=0.0)
        con = calcular(self.camaras, 7, 60, margen=0.15)
        self.assertAlmostEqual(con.tb_con_margen, sin.tb_total * 1.15, places=6)

    def test_bitrates_mixtos_se_suman_por_camara(self):
        mixtas = [
            Camara("frente_4k", 8.0, fraccion_eventos=0.10),
            Camara("patio_2k", 4.0, fraccion_eventos=0.10),
        ]
        r = calcular(mixtas, dias_continua=7, dias_eventos=7, margen=0.0)
        esperado = tb_continua(8.0, 1, 7) + tb_continua(4.0, 1, 7)
        self.assertAlmostEqual(r.tb_total, esperado, places=6)

    def test_camara_a_la_via_publica_dispara_los_eventos(self):
        """Una camara que mira a la calle puede superar 0,30 de fraccion de evento."""
        tranquila = calcular([Camara("patio", 8.0, fraccion_eventos=0.05)], 7, 60, margen=0.0)
        calle = calcular([Camara("calle", 8.0, fraccion_eventos=0.35)], 7, 60, margen=0.0)
        self.assertGreater(calle.tb_total, tranquila.tb_total * 2)


class EntradasInvalidas(unittest.TestCase):
    def test_bitrate_negativo(self):
        with self.assertRaises(ValueError):
            tb_por_camara_dia(-1)

    def test_dias_negativos(self):
        with self.assertRaises(ValueError):
            tb_continua(8.0, 4, -1)

    def test_ventana_de_eventos_mas_corta_que_la_continua(self):
        """Configuracion incoherente: la purga continua se llevaria los eventos por delante."""
        with self.assertRaises(ValueError):
            calcular([Camara("c", 8.0)], dias_continua=30, dias_eventos=7)

    def test_fraccion_de_eventos_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            calcular([Camara("c", 8.0, fraccion_eventos=1.5)], 7, 30)


class SinCamaras(unittest.TestCase):
    def test_instalacion_sin_camaras_no_revienta(self):
        r = calcular([], dias_continua=7, dias_eventos=30)
        self.assertEqual(r.tb_total, 0.0)
        self.assertEqual(r.gb_por_dia, 0.0)


if __name__ == "__main__":
    unittest.main()
