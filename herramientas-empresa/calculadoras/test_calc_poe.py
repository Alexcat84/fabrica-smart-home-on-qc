"""Pruebas de la calculadora de presupuesto PoE.

La regla que estas pruebas protegen: **40 % de holgura sobre el peor caso**. Un presupuesto ajustado
produce caidas intermitentes de camara de noche, en invierno, que solo se manifiestan cuando el
infrarrojo y el calefactor tiran a la vez. Es el fallo mas caro de diagnosticar del catalogo.
"""

import unittest

from calc_poe import HOLGURA_MINIMA, DispositivoPoE, calcular


class ReglaDeHolgura(unittest.TestCase):
    def test_switch_justo_al_limite_cumple(self):
        d = [DispositivoPoE("cam1", "camara_4k_ir")]        # 13 W
        r = calcular(d, presupuesto_switch_w=13 * 1.4)
        self.assertTrue(r.cumple)
        self.assertAlmostEqual(r.holgura_real, HOLGURA_MINIMA, places=6)

    def test_switch_un_vatio_por_debajo_no_cumple(self):
        d = [DispositivoPoE("cam1", "camara_4k_ir")]
        r = calcular(d, presupuesto_switch_w=13 * 1.4 - 1)
        self.assertFalse(r.cumple)

    def test_holgura_del_30_por_ciento_no_basta(self):
        """El error clasico: dimensionar con 30 % y quedarse corto la primera helada."""
        d = [DispositivoPoE(f"cam{i}", "camara_4k_ir_calefactor") for i in range(6)]  # 150 W
        r = calcular(d, presupuesto_switch_w=150 * 1.30)
        self.assertFalse(r.cumple)
        self.assertAlmostEqual(r.requerido_w, 210.0, places=1)


class PeorCasoInvernal(unittest.TestCase):
    def test_el_calefactor_casi_duplica_el_consumo_de_la_camara(self):
        sin = calcular([DispositivoPoE("c", "camara_4k_ir")], 100)
        con = calcular([DispositivoPoE("c", "camara_4k_ir_calefactor")], 100)
        self.assertGreater(con.peor_caso_w, sin.peor_caso_w * 1.8)

    def test_instalacion_tipica_de_paquete_m(self):
        """5 camaras 4K con IR, 2 puntos de acceso y un coordinador Zigbee."""
        dispositivos = (
            [DispositivoPoE(f"cam{i}", "camara_4k_ir") for i in range(5)]      # 65 W
            + [DispositivoPoE(f"ap{i}", "punto_acceso") for i in range(2)]     # 40 W
            + [DispositivoPoE("zigbee", "coordinador_zigbee")]                 #  4 W
        )
        r = calcular(dispositivos, presupuesto_switch_w=180)
        self.assertAlmostEqual(r.peor_caso_w, 109.0, places=1)
        self.assertAlmostEqual(r.requerido_w, 152.6, places=1)
        self.assertTrue(r.cumple)
        self.assertEqual(r.puertos_usados, 8)

    def test_la_misma_instalacion_con_calefactores_no_cabe_en_el_mismo_switch(self):
        dispositivos = (
            [DispositivoPoE(f"cam{i}", "camara_4k_ir_calefactor") for i in range(5)]  # 125 W
            + [DispositivoPoE(f"ap{i}", "punto_acceso") for i in range(2)]            #  40 W
            + [DispositivoPoE("zigbee", "coordinador_zigbee")]                        #   4 W
        )
        r = calcular(dispositivos, presupuesto_switch_w=180)
        self.assertFalse(r.cumple)


class ConsumoVerificado(unittest.TestCase):
    def test_el_dato_de_ficha_tecnica_sustituye_al_tipico(self):
        r = calcular([DispositivoPoE("cam", "camara_4k_ir", consumo_w=9.5)], 100)
        self.assertEqual(r.peor_caso_w, 9.5)
        self.assertFalse(r.hay_estimaciones)

    def test_se_avisa_cuando_hay_estimaciones(self):
        r = calcular([DispositivoPoE("cam", "camara_4k_ir")], 100)
        self.assertTrue(r.hay_estimaciones)
        self.assertIn("estimados", r.resumen())

    def test_mezcla_de_verificados_y_estimados_avisa_igual(self):
        r = calcular(
            [
                DispositivoPoE("a", "camara_4k_ir", consumo_w=9.5),
                DispositivoPoE("b", "camara_4k_ir"),
            ],
            100,
        )
        self.assertTrue(r.hay_estimaciones)


class EntradasInvalidas(unittest.TestCase):
    def test_tipo_desconocido(self):
        with self.assertRaises(ValueError) as ctx:
            calcular([DispositivoPoE("x", "camara_de_seguridad_generica")], 100)
        self.assertIn("tipo PoE desconocido", str(ctx.exception))

    def test_presupuesto_cero(self):
        with self.assertRaises(ValueError):
            calcular([DispositivoPoE("cam", "camara_2k")], 0)

    def test_sin_dispositivos_la_holgura_es_infinita(self):
        r = calcular([], presupuesto_switch_w=100)
        self.assertEqual(r.peor_caso_w, 0.0)
        self.assertTrue(r.cumple)


if __name__ == "__main__":
    unittest.main()
