"""Pruebas de la calculadora de ancho de banda de subida.

Tres roles de flujo y tres escenarios (ADR-012). Lo que protegen: que el diseno no prometa
visionado remoto que el enlace del sitio no puede sostener, y que la penalizacion de una camara de
dos flujos se pague en el calculo y no en la cara del cliente.

  1. Cuadricula remota      N visores sobre `sub`                 -> vinculante
  2. Apertura de una camara sobre `medio`, o sobre `principal`
                            si la camara solo publica dos flujos  -> vinculante
  3. Apertura sobre `principal`                                   -> advierte, no rechaza
"""

import unittest

from calc_ancho_banda import (
    MARGEN_HOGAR_MBPS,
    CamaraAB,
    SubstreamSinMedir,
    calcular,
    desde_cliente,
    resolver_camara,
)


def cam(nombre="cam", principal=8.0, sub=0.5, medio=2.0, streams=3, origen="cliente"):
    return CamaraAB(nombre, principal, sub, medio, streams, origen, origen)


def cam2(nombre="cam2f", principal=8.0, sub=0.5):
    """Camara de dos flujos: sin intermedio util."""
    return CamaraAB(nombre, principal, sub, None, 2, "cliente", "desconocido")


# =================================================================================================
# Resolucion de los flujos contra el catalogo
# =================================================================================================

class ResolucionDeFlujos(unittest.TestCase):
    CAT = {
        "substream_bitrate_mbps": 0.6,
        "stream_medio_bitrate_mbps": 2.5,
        "streams_soportados": 3,
    }

    def test_el_cliente_manda_sobre_el_catalogo(self):
        c = resolver_camara(
            {"nombre": "c", "bitrate_principal_mbps": 8.0, "bitrate_substream_mbps": 0.4,
             "bitrate_medio_mbps": 1.8, "streams_soportados": 3},
            self.CAT,
        )
        self.assertEqual(c.sub_mbps, 0.4)
        self.assertEqual(c.medio_mbps, 1.8)
        self.assertEqual(c.origen_sub, "cliente")

    def test_cae_al_catalogo_cuando_el_cliente_no_lo_declara(self):
        c = resolver_camara({"nombre": "c", "bitrate_principal_mbps": 8.0}, self.CAT)
        self.assertEqual(c.sub_mbps, 0.6)
        self.assertEqual(c.medio_mbps, 2.5)
        self.assertEqual(c.origen_sub, "catalogo")

    def test_sin_substream_medido_falla(self):
        with self.assertRaises(SubstreamSinMedir) as ctx:
            resolver_camara({"nombre": "c", "bitrate_principal_mbps": 8.0, "streams_soportados": 3}, {})
        self.assertIn("SUB-STREAM", str(ctx.exception))

    def test_sin_streams_soportados_falla(self):
        """Sin ese dato no se sabe si abrir una camara sirve un intermedio o el principal."""
        with self.assertRaises(SubstreamSinMedir) as ctx:
            resolver_camara(
                {"nombre": "c", "bitrate_principal_mbps": 8.0, "bitrate_substream_mbps": 0.5}, {}
            )
        self.assertIn("streams_soportados", str(ctx.exception))
        self.assertIn("M-14", str(ctx.exception))

    def test_declarar_tres_flujos_sin_medir_el_medio_falla(self):
        """Incoherencia: dice tener tres flujos y no dice cuanto pesa el tercero."""
        with self.assertRaises(SubstreamSinMedir) as ctx:
            resolver_camara(
                {"nombre": "c", "bitrate_principal_mbps": 8.0, "bitrate_substream_mbps": 0.5,
                 "streams_soportados": 3}, {},
            )
        self.assertIn("flujo MEDIO", str(ctx.exception))

    def test_dos_flujos_no_exige_medio(self):
        c = resolver_camara(
            {"nombre": "c", "bitrate_principal_mbps": 8.0, "bitrate_substream_mbps": 0.5,
             "streams_soportados": 2}, {},
        )
        self.assertFalse(c.tiene_flujo_medio)
        self.assertEqual(c.bitrate_de_apertura_mbps, 8.0)


# =================================================================================================
# Escenario 1: cuadricula remota
# =================================================================================================

class EscenarioCuadricula(unittest.TestCase):
    def test_todos_los_sub_por_todos_los_visores(self):
        r = calcular([cam(sub=0.5) for _ in range(5)], 2, subida_disponible_mbps=25.0)
        self.assertEqual(r.sub_total_mbps, 5.0)
        self.assertEqual(r.requerido_cuadricula_mbps, 10.0)
        self.assertTrue(r.cumple_cuadricula)

    def test_sin_margen_el_calculo_miente(self):
        justo = calcular([cam(sub=1.0) for _ in range(5)], 2,
                         subida_disponible_mbps=10.0, margen_hogar_mbps=0.0)
        real = calcular([cam(sub=1.0) for _ in range(5)], 2,
                        subida_disponible_mbps=10.0, margen_hogar_mbps=5.0)
        self.assertTrue(justo.cumple_cuadricula)
        self.assertFalse(real.cumple_cuadricula)


# =================================================================================================
# Escenario 2: apertura de una camara
# =================================================================================================

class EscenarioApertura(unittest.TestCase):
    def test_con_flujo_medio_el_salto_es_pequeno(self):
        """Es el motivo entero de ADR-012: 1,5 Mbps en lugar de 7,5."""
        camaras = [cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(5)]
        r = calcular(camaras, 2, subida_disponible_mbps=15.0)
        self.assertEqual(r.salto_apertura_mbps, 1.5)
        self.assertEqual(r.requerido_apertura_mbps, 11.5)
        self.assertTrue(r.cumple_apertura)
        self.assertFalse(r.apertura_usa_principal)

    def test_sin_flujo_medio_la_apertura_usa_el_principal_y_rechaza(self):
        """La penalizacion real de una camara de dos flujos, pagada en el calculo."""
        camaras = [cam2(principal=8.0, sub=0.5) for _ in range(5)]
        r = calcular(camaras, 2, subida_disponible_mbps=15.0)
        self.assertTrue(r.apertura_usa_principal)
        self.assertEqual(r.salto_apertura_mbps, 7.5)
        self.assertEqual(r.requerido_apertura_mbps, 17.5)
        self.assertFalse(r.cumple_apertura)
        self.assertFalse(r.cumple, "el resultado global exige los escenarios 1 y 2")

    def test_una_sola_camara_de_dos_flujos_marca_el_peor_caso(self):
        """No se sabe cual va a tocar el visor, asi que manda la peor."""
        camaras = [cam("a", principal=8.0, medio=2.0), cam2("garaje", principal=4.0)]
        r = calcular(camaras, 1, subida_disponible_mbps=25.0)
        self.assertEqual(r.camara_de_apertura, "garaje")
        self.assertEqual(r.salto_apertura_mbps, 3.5)
        self.assertTrue(r.apertura_usa_principal)
        self.assertEqual(r.camaras_de_dos_flujos, ["garaje"])

    def test_el_salto_descuenta_el_sub_que_deja_de_pedir(self):
        r = calcular([cam(principal=8.0, medio=3.0, sub=1.0)], 1, subida_disponible_mbps=25.0)
        self.assertEqual(r.salto_apertura_mbps, 2.0)


# =================================================================================================
# Escenario 3: apertura sobre principal, excepcion bajo demanda
# =================================================================================================

class EscenarioPrincipalBajoDemanda(unittest.TestCase):
    def test_advierte_pero_no_rechaza(self):
        """Rechazar por el obligaria a contratar enlaces que nadie necesita el 99 % del tiempo."""
        camaras = [cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(5)]
        r = calcular(camaras, 2, subida_disponible_mbps=15.0)
        self.assertEqual(r.requerido_principal_mbps, 17.5)
        self.assertFalse(r.cabe_principal, "no cabe en 15 Mbps")
        self.assertTrue(r.cumple, "y aun asi el cliente valida: es excepcion bajo demanda")

    def test_el_resumen_explica_que_no_es_un_defecto(self):
        camaras = [cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(5)]
        texto = calcular(camaras, 2, subida_disponible_mbps=15.0).resumen()
        self.assertIn("excepcion", texto.lower())
        self.assertIn("ADR-012", texto)

    def test_con_fibra_simetrica_cabe(self):
        camaras = [cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(5)]
        r = calcular(camaras, 2, subida_disponible_mbps=50.0)
        self.assertTrue(r.cabe_principal)


# =================================================================================================
# Minimos publicados por paquete
# =================================================================================================

class MinimosPublicados(unittest.TestCase):
    """Los minimos de comercial/paquetes/ tienen que sostener los dos escenarios vinculantes."""

    def _vinculante(self, camaras, visores, margen=5.0):
        r = calcular(camaras, visores, subida_disponible_mbps=10_000, margen_hogar_mbps=margen)
        return max(r.requerido_cuadricula_mbps, r.requerido_apertura_mbps)

    def test_paquete_s_cabe_en_5_mbps(self):
        camaras = [cam(principal=4.0, medio=1.2, sub=0.5) for _ in range(3)]
        self.assertLessEqual(self._vinculante(camaras, 1, margen=2.0), 5.0)

    def test_paquete_m_cabe_en_15_y_NO_en_los_10_de_antes(self):
        """El hallazgo: el minimo publicado de M estaba por debajo del uso normal."""
        camaras = ([cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(2)]
                   + [cam(principal=4.0, medio=1.2, sub=0.5) for _ in range(3)])
        vinculante = self._vinculante(camaras, 2)
        self.assertLessEqual(vinculante, 15.0)
        self.assertGreater(vinculante, 10.0, "los 10 Mbps publicados antes no bastaban")

    def test_paquete_l_cabe_en_20(self):
        camaras = [cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(10)]
        self.assertLessEqual(self._vinculante(camaras, 2), 20.0)

    def test_paquete_xl_cabe_en_40(self):
        camaras = [cam(principal=8.0, medio=2.0, sub=0.5) for _ in range(18)]
        self.assertLessEqual(self._vinculante(camaras, 3), 40.0)


# =================================================================================================
# Casos limite y entradas invalidas
# =================================================================================================

class CasosLimite(unittest.TestCase):
    def test_sin_camaras_solo_queda_el_margen(self):
        r = calcular([], 1, subida_disponible_mbps=5.0)
        self.assertEqual(r.sub_total_mbps, 0.0)
        self.assertEqual(r.requerido_cuadricula_mbps, MARGEN_HOGAR_MBPS)
        self.assertEqual(r.salto_apertura_mbps, 0.0)
        self.assertTrue(r.cumple)

    def test_sin_visores_no_hay_apertura(self):
        r = calcular([cam()], 0, subida_disponible_mbps=5.0)
        self.assertEqual(r.salto_apertura_mbps, 0.0)
        self.assertTrue(r.cumple)

    def test_se_avisa_cuando_el_dato_viene_del_catalogo(self):
        r = calcular([cam(origen="catalogo")], 1, subida_disponible_mbps=25.0)
        self.assertTrue(r.hay_datos_de_catalogo)


class EntradasInvalidas(unittest.TestCase):
    def test_subida_cero_es_error_no_resultado(self):
        with self.assertRaises(ValueError) as ctx:
            calcular([cam()], 1, subida_disponible_mbps=0)
        self.assertIn("relevamiento", str(ctx.exception))

    def test_visores_negativos(self):
        with self.assertRaises(ValueError):
            calcular([cam()], -1, subida_disponible_mbps=25.0)


class DesdeCliente(unittest.TestCase):
    CATALOGO = [
        {"id": "cam-3f", "substream_bitrate_mbps": 0.6, "stream_medio_bitrate_mbps": 2.0,
         "streams_soportados": 3},
        {"id": "cam-2f", "substream_bitrate_mbps": 0.6, "stream_medio_bitrate_mbps": None,
         "streams_soportados": 2},
    ]

    def test_lee_los_tres_flujos_del_catalogo(self):
        cliente = {
            "camaras": [{"nombre": "c1", "id_catalogo": "cam-3f", "bitrate_principal_mbps": 8.0}],
            "visores_concurrentes": 1,
            "red": {"subida_mbps": 25.0},
        }
        r = desde_cliente(cliente, self.CATALOGO)
        self.assertAlmostEqual(r.sub_total_mbps, 0.6, places=2)
        self.assertAlmostEqual(r.salto_apertura_mbps, 1.4, places=2)
        self.assertFalse(r.apertura_usa_principal)

    def test_una_camara_de_dos_flujos_del_catalogo_cambia_el_escenario_2(self):
        cliente = {
            "camaras": [{"nombre": "c2", "id_catalogo": "cam-2f", "bitrate_principal_mbps": 8.0}],
            "visores_concurrentes": 1,
            "red": {"subida_mbps": 25.0},
        }
        r = desde_cliente(cliente, self.CATALOGO)
        self.assertTrue(r.apertura_usa_principal)
        self.assertAlmostEqual(r.salto_apertura_mbps, 7.4, places=2)


if __name__ == "__main__":
    unittest.main()
