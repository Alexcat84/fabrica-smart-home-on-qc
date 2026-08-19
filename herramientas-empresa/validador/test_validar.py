"""Pruebas de regresion del validador.

Estas pruebas comprueban lo que el validador tiene que RECHAZAR. Una regla que no rechaza nada es
una regla que no existe, y este archivo es la prueba de que las cinco reglas inviolables de
`docs/DECISIONES.md` siguen teniendo dientes.

Cada caso parte del cliente de demostracion, que valida limpio, y le introduce exactamente un
defecto. Asi el fallo que se observa es atribuible a ese defecto y no a otra cosa.

    python -m unittest discover -s herramientas-empresa/validador -p "test_*.py"
"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "herramientas-empresa" / "validador"))

import validar  # noqa: E402

DEMO = RAIZ / "clientes" / "EJEMPLO-demo" / "cliente.yaml"


def cliente_base() -> dict:
    with open(DEMO, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validar_dict(datos: dict) -> validar.Informe:
    """Escribe el cliente a disco y lo valida, como haria el flujo real."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "cliente.yaml"
        ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
        inf, _ = validar.validar_cliente(ruta)
        return inf


def hay_error_con(inf: validar.Informe, fragmento: str) -> bool:
    return any(fragmento in e for e in inf.errores)


class ElDemoValidaLimpio(unittest.TestCase):
    """Si esto falla, el resto de pruebas no significan nada."""

    def test_el_cliente_de_demostracion_no_tiene_errores(self):
        inf, _ = validar.validar_cliente(DEMO)
        self.assertTrue(inf.valido, f"El demo deberia validar. Errores: {inf.errores}")


class ADR001_CatalogoObligatorio(unittest.TestCase):
    def test_dispositivo_fuera_del_catalogo(self):
        d = cliente_base()
        d["dispositivos"][0]["id_catalogo"] = "interruptor-que-nadie-ha-evaluado"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "no existe en datos-maestros/dispositivos/"))

    def test_dispositivo_sin_id_de_catalogo(self):
        d = cliente_base()
        del d["dispositivos"][0]["id_catalogo"]
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "no declara `id_catalogo`"))

    def test_dispositivo_del_registro_de_exclusion(self):
        """Lo mas probable en la practica: alguien encuentra el Sonoff en un foro."""
        d = cliente_base()
        d["dispositivos"][0]["id_catalogo"] = "sonoff-zbminil2"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "REGISTRO DE EXCLUSION"))

    def test_componente_de_software_fuera_del_catalogo(self):
        d = cliente_base()
        d["software_desplegado"].append("un-componente-cualquiera")
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "no existe en datos-maestros/software-cliente.yaml"))


class ADR002_CertificacionCanadiense(unittest.TestCase):
    def test_instalable_en_caja_sin_certificacion_verificada(self):
        d = cliente_base()
        del d["dispositivos"][0]["certificacion_verificada"]
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "certificacion esta sin verificar"))

    def test_marca_europea_no_vale(self):
        d = cliente_base()
        d["dispositivos"][0]["certificacion_verificada"]["marca"] = "CE"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "no es"))
        self.assertTrue(hay_error_con(inf, "marca canadiense valida"))

    def test_verificacion_sin_autor_ni_fecha_no_es_trazable(self):
        d = cliente_base()
        del d["dispositivos"][0]["certificacion_verificada"]["verificado_por"]
        del d["dispositivos"][0]["certificacion_verificada"]["fecha"]
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "verificacion"))
        self.assertTrue(hay_error_con(inf, "incompleta"))

    def test_la_verificacion_ficticia_no_se_filtra_a_un_cliente_real(self):
        """El fallo que esta prueba evita: copiar el demo para arrancar un cliente de verdad."""
        d = cliente_base()
        d["es_ejemplo"] = False
        d["cliente"]["id"] = "APELLIDO-ottawa"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "EJEMPLO-NO-REAL"))


class ADR004_SinSeguridadDeVida(unittest.TestCase):
    def test_sensor_llamado_detector_de_humo(self):
        d = cliente_base()
        d["dispositivos"][0]["nombre"] = "sensor_humo_planta_baja"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "ADR-004"))

    def test_automatizacion_llamada_alarma(self):
        d = cliente_base()
        d["dispositivos"][0]["nombre_cliente"] = "Intrusion alarm"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "ADR-004"))

    def test_camara_llamada_de_emergencia(self):
        d = cliente_base()
        d["camaras"][0]["nombre"] = "camara_emergencia_frente"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "ADR-004"))

    def test_termino_frances_tambien_salta(self):
        d = cliente_base()
        d["dispositivos"][0]["nombre_cliente"] = "Detecteur incendie"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "ADR-004"))

    def test_calidad_de_aire_es_legitimo_y_no_salta(self):
        """`gas` esta vetado, pero `calidad_aire` no puede saltar: es el nombre correcto."""
        d = cliente_base()
        d["dispositivos"][0]["nombre"] = "sensor_calidad_aire_planta_baja"
        d["dispositivos"][0]["nombre_cliente"] = "Air quality"
        inf = validar_dict(d)
        self.assertFalse(hay_error_con(inf, "ADR-004"))

    def test_disuasion_es_legitimo_y_no_salta(self):
        d = cliente_base()
        d["dispositivos"][0]["nombre_cliente"] = "Deterrent siren"
        inf = validar_dict(d)
        self.assertFalse(hay_error_con(inf, "ADR-004"))


class Dimensionado(unittest.TestCase):
    def test_almacenamiento_insuficiente_para_la_retencion_pedida(self):
        d = cliente_base()
        d["retencion"]["continua_dias"] = 30
        d["retencion"]["eventos_dias"] = 90
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "no alcanza la retencion pedida"))

    def test_almacenamiento_sin_declarar(self):
        d = cliente_base()
        d["almacenamiento"]["vigilancia_tb"] = None
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "vigilancia_tb"))

    def test_poe_sin_la_holgura_del_40_por_ciento(self):
        d = cliente_base()
        d["poe"]["presupuesto_switch_w"] = 120
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "40 % de holgura"))

    def test_poe_sin_presupuesto_declarado(self):
        d = cliente_base()
        d["poe"]["presupuesto_switch_w"] = None
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "presupuesto_switch_w"))

    def test_escenario_1_subida_insuficiente_en_vista_general(self):
        d = cliente_base()
        d["visores_concurrentes"] = 12
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "ESCENARIO 1"))

    def test_escenario_2_subida_insuficiente_al_escalar_a_principal(self):
        """M-12. La vista general cabe; abrir una camara en principal, no.

        Es el caso que la primera version del validador dejaba pasar: el minimo publicado del
        paquete solo cubre mirar, no cubre mirar de cerca.
        """
        d = cliente_base()
        d["red"]["subida_mbps"] = 15.0     # supera el minimo del paquete M, y aun asi no basta
        inf = validar_dict(d)
        self.assertFalse(hay_error_con(inf, "ESCENARIO 1"), "la vista general si cabe en 15 Mbps")
        self.assertTrue(hay_error_con(inf, "ESCENARIO 2"))

    def test_camara_sin_substream_medido_se_rechaza(self):
        """No se supone un bitrate de sub-stream: sin medicion, el cliente no valida (ADR-001)."""
        d = cliente_base()
        for cam in d["camaras"]:
            cam.pop("bitrate_substream_mbps", None)
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "sub-stream"))
        self.assertTrue(hay_error_con(inf, "ADR-001"))

    def test_subida_por_debajo_del_minimo_del_paquete(self):
        d = cliente_base()
        d["red"]["subida_mbps"] = 6.0
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "por debajo del minimo del paquete"))


class Red(unittest.TestCase):
    def test_octeto_sin_declarar(self):
        d = cliente_base()
        d["red"]["octeto"] = None
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "red.octeto"))

    def test_octeto_fuera_de_rango(self):
        d = cliente_base()
        d["red"]["octeto"] = 300
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "fuera del rango"))

    def test_colision_de_octeto_con_otro_cliente(self):
        """El demo ya usa el 99. Otro cliente con el mismo octeto tiene que saltar."""
        d = cliente_base()
        d["cliente"]["id"] = "OTRO-cliente"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "COLISION DE OCTETO"))

    def test_paquete_inexistente(self):
        d = cliente_base()
        d["paquete"] = "XXL"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "no existe en comercial/paquetes/"))


class ADR005_SinSecretos(unittest.TestCase):
    def test_contrasena_en_el_archivo_de_cliente(self):
        d = cliente_base()
        d["mqtt"]["password"] = "una-contrasena-de-verdad-aqui"
        inf = validar_dict(d)
        self.assertTrue(hay_error_con(inf, "ADR-005"))

    def test_el_marcador_de_comisionamiento_no_salta(self):
        d = cliente_base()
        d["mqtt"]["password"] = "CAMBIAR-EN-COMISIONAMIENTO"
        inf = validar_dict(d)
        self.assertFalse(hay_error_con(inf, "ADR-005"))


class Catalogo(unittest.TestCase):
    def test_el_catalogo_es_internamente_coherente(self):
        inf = validar.Informe()
        validar.validar_catalogo(inf)
        self.assertTrue(inf.valido, f"El catalogo no valida: {inf.errores}")


if __name__ == "__main__":
    unittest.main()
