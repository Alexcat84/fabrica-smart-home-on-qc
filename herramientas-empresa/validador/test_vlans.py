"""Pruebas de regresion del recuento de VLAN por paquete.

Existen porque el plan de negocio de origen se contradecia a si mismo (fila M-08, cerrada por
ADR-009): el cap. 8.1 fijaba 4/5/6/6 VLAN para S/M/L/XL, y el cap. 8.2.1 describia Management y
Guest como presentes "de M en adelante", lo que daria seis en M.

La decision esta tomada. Estas pruebas impiden que la contradiccion vuelva a entrar sin que algo
falle, y comprueban el recuento **sobre la plantilla renderizada**, no sobre la definicion del
paquete: lo que importa es lo que el generador produce, no lo que el YAML declara.

    python -m unittest discover -s herramientas-empresa/validador -p "test_*.py"
"""

import sys
import unittest
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "herramientas-empresa" / "validador"))

import validar  # noqa: E402

DEMO = RAIZ / "clientes" / "EJEMPLO-demo" / "cliente.yaml"

# ADR-009. Lo que cada paquete debe producir.
ESPERADO = {
    "S":  {"cantidad": 4, "presentes": [10, 20, 30, 40],             "ausentes": [50, 60]},
    "M":  {"cantidad": 5, "presentes": [10, 20, 30, 40, 60],         "ausentes": [50]},
    "L":  {"cantidad": 6, "presentes": [10, 20, 30, 40, 50, 60],     "ausentes": []},
    "XL": {"cantidad": 6, "presentes": [10, 20, 30, 40, 50, 60],     "ausentes": []},
}


def renderizar_vlans(id_paquete: str) -> dict:
    """Renderiza plantillas/red/vlans.yaml.j2 para un paquete y devuelve el YAML resultante.

    Se parte del cliente de demostracion y solo se cambia el paquete: asi la unica variable entre
    los cuatro casos es la que se esta probando.
    """
    cliente = yaml.safe_load(DEMO.read_text(encoding="utf-8"))
    cliente["paquete"] = id_paquete

    paquete = validar.cargar_paquete(id_paquete)
    assert paquete is not None, f"El paquete {id_paquete} no existe en comercial/paquetes/"

    env = Environment(
        loader=FileSystemLoader(str(RAIZ / "producto-cliente")),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    ctx = dict(cliente)
    ctx["paquete_def"] = paquete
    ctx["generado_en"] = "prueba"
    salida = env.get_template("stack/red/vlans.yaml.j2").render(**ctx)
    return yaml.safe_load(salida)


class RecuentoDeVlanPorPaquete(unittest.TestCase):
    """Una prueba por paquete, como pide ADR-009."""

    def _comprobar(self, id_paquete: str) -> None:
        esperado = ESPERADO[id_paquete]
        datos = renderizar_vlans(id_paquete)

        presentes = sorted(v["id"] for v in datos["vlans"] if v.get("presente"))
        ausentes = sorted(v["id"] for v in datos["vlans"] if not v.get("presente"))

        self.assertEqual(
            presentes, esperado["presentes"],
            f"{id_paquete}: VLAN presentes en la plantilla renderizada",
        )
        self.assertEqual(
            ausentes, esperado["ausentes"],
            f"{id_paquete}: VLAN ausentes en la plantilla renderizada",
        )
        self.assertEqual(
            len(presentes), esperado["cantidad"],
            f"{id_paquete}: el recuento debe ser {esperado['cantidad']}",
        )

        # El paquete y la plantilla no pueden discrepar entre si.
        paquete = validar.cargar_paquete(id_paquete)
        self.assertEqual(
            paquete["vlans"]["cantidad"], esperado["cantidad"],
            f"{id_paquete}: paquetes/*.yaml discrepa de la plantilla renderizada",
        )

    def test_paquete_s_tiene_4_vlan(self):
        self._comprobar("S")

    def test_paquete_m_tiene_5_vlan(self):
        self._comprobar("M")

    def test_paquete_l_tiene_6_vlan(self):
        self._comprobar("L")

    def test_paquete_xl_tiene_6_vlan(self):
        self._comprobar("XL")


class ManagementSeDespliegaDeLEnAdelante(unittest.TestCase):
    """El nucleo de ADR-009, comprobado explicitamente."""

    def test_management_ausente_en_s_y_m(self):
        for id_paquete in ("S", "M"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                mgmt = next(v for v in datos["vlans"] if v["id"] == 50)
                self.assertFalse(mgmt["presente"])
                self.assertEqual(
                    mgmt["plegada_en"], 40,
                    "Management debe declararse plegada en Controller, no simplemente omitida",
                )

    def test_management_presente_en_l_y_xl(self):
        for id_paquete in ("L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                mgmt = next(v for v in datos["vlans"] if v["id"] == 50)
                self.assertTrue(mgmt["presente"])

    def test_plegar_management_no_elimina_la_regla_de_cortafuegos(self):
        """Plegar la VLAN reduce segmentos, no politica.

        Si alguien "simplifica" el nivel S borrando las reglas que nombran Management, el acceso
        administrativo queda abierto desde Trusted. Esta prueba lo impide.
        """
        env = Environment(
            loader=FileSystemLoader(str(RAIZ / "producto-cliente")),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        cliente = yaml.safe_load(DEMO.read_text(encoding="utf-8"))
        cliente["paquete"] = "S"
        ctx = dict(cliente)
        ctx["paquete_def"] = validar.cargar_paquete("S")
        ctx["generado_en"] = "prueba"
        datos = yaml.safe_load(env.get_template("stack/red/firewall.yaml.j2").render(**ctx))

        ids = {r["id"] for r in datos["reglas"]}
        self.assertIn("trusted_a_management", ids)
        self.assertIn("iot_a_management", ids)

        trusted = next(r for r in datos["reglas"] if r["id"] == "trusted_a_management")
        self.assertEqual(trusted["accion"], "denegar")


class GuestSeDespliegaDeMEnAdelante(unittest.TestCase):
    def test_guest_ausente_solo_en_s(self):
        datos = renderizar_vlans("S")
        guest = next(v for v in datos["vlans"] if v["id"] == 60)
        self.assertFalse(guest["presente"])

    def test_guest_presente_de_m_en_adelante(self):
        for id_paquete in ("M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                guest = next(v for v in datos["vlans"] if v["id"] == 60)
                self.assertTrue(guest["presente"])

    def test_guest_lleva_aislamiento_de_clientes(self):
        datos = renderizar_vlans("M")
        guest = next(v for v in datos["vlans"] if v["id"] == 60)
        self.assertTrue(guest["aislamiento_de_clientes"])


if __name__ == "__main__":
    unittest.main()
