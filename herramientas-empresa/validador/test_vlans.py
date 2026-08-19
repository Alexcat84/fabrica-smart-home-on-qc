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
                    mgmt["plegada_en"], 10,
                    "Management se pliega en TRUSTED, no simplemente se omite (enmienda de ADR-009)",
                )

    def test_management_no_se_pliega_nunca_en_controller(self):
        """Enmienda de ADR-009. El motivo esta en el ADR y merece prueba propia.

        Plegar la gestion de red dentro del segmento del controlador le daba alcance administrativo
        sobre la pasarela y los switches. Como el controlador es el equipo que contiene las camaras,
        eso convertia un compromiso del grabador en un compromiso de la red entera.
        """
        for id_paquete in ("S", "M"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                mgmt = next(v for v in datos["vlans"] if v["id"] == 50)
                self.assertNotEqual(
                    mgmt["plegada_en"], 40,
                    "Management NO puede plegarse en Controller: el controlador contiene las "
                    "camaras y no debe alcanzar la infraestructura de red",
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


class ControllerNuncaAlcanzaManagement(unittest.TestCase):
    """Regla que NO depende del nivel (enmienda de ADR-009).

    El anfitrion del controlador es el objetivo de mayor valor de la instalacion porque contiene las
    camaras y su grabacion. Darle alcance administrativo sobre la pasarela y los switches
    convertiria un compromiso del grabador en un compromiso de la infraestructura entera.

    Se comprueba en los CUATRO paquetes, este la VLAN plegada o separada.
    """

    def _reglas(self, id_paquete: str) -> dict:
        env = Environment(
            loader=FileSystemLoader(str(RAIZ / "producto-cliente")),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        cliente = yaml.safe_load(DEMO.read_text(encoding="utf-8"))
        cliente["paquete"] = id_paquete
        ctx = dict(cliente)
        ctx["paquete_def"] = validar.cargar_paquete(id_paquete)
        ctx["generado_en"] = "prueba"
        datos = yaml.safe_load(env.get_template("stack/red/firewall.yaml.j2").render(**ctx))
        return {r["id"]: r for r in datos["reglas"]}

    def test_controller_a_management_denegado_en_los_cuatro_paquetes(self):
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                reglas = self._reglas(id_paquete)
                self.assertIn(
                    "controller_a_management", reglas,
                    f"{id_paquete}: la regla no puede desaparecer al plegar la VLAN",
                )
                self.assertEqual(
                    reglas["controller_a_management"]["accion"], "denegar",
                    f"{id_paquete}: Controller nunca alcanza Management",
                )

    def test_el_destino_resuelve_a_direcciones_concretas_en_los_cuatro_paquetes(self):
        """LA PRUEBA QUE FALTABA, y el motivo de que exista `grupo_gestion`.

        Las otras dos pruebas de esta clase pasaban con un destino que no resolvia a nada. En S y M,
        `destino: Management` nombraba un segmento que no existe -la VLAN 50 esta plegada- y la
        regla daba cobertura aparente: parecia proteger y no protegia. Lo que de hecho protegia era
        `controller_a_trusted: denegar`, que es una regla distinta.

        Que la regla exista no basta. Su destino tiene que ser algo que el cortafuegos pueda
        traducir a direcciones.
        """
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                regla = self._reglas(id_paquete)["controller_a_management"]
                direcciones = regla.get("destino_direcciones") or []
                subred = regla.get("destino_subred")
                self.assertTrue(
                    direcciones or subred,
                    f"{id_paquete}: `controller_a_management` no resuelve a ninguna direccion ni "
                    f"subred. El destino es '{regla.get('destino')}', que en este nivel no existe.",
                )
                for d in direcciones:
                    self.assertRegex(d, r"^\d+\.\d+\.\d+\.\d+$", f"{id_paquete}: '{d}' no es una IP")

    def test_los_hosts_de_gestion_estan_materializados_al_plegar(self):
        """Plegar la VLAN obliga a enumerar sus hosts, o la regla se queda sin destino."""
        for id_paquete in ("S", "M"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                grupo = datos.get("grupo_gestion")
                self.assertIsNotNone(grupo, f"{id_paquete}: falta `grupo_gestion` en vlans.yaml")
                self.assertEqual(grupo["tipo"], "direcciones")
                self.assertEqual(grupo["vlan_receptora"], 10)

                nombres = {m["nombre"] for m in grupo["miembros"]}
                for esperado in ("pasarela", "switch_principal", "interfaz_fuera_de_banda"):
                    self.assertIn(esperado, nombres, f"{id_paquete}: falta {esperado} en el grupo")
                self.assertTrue(
                    any(n.startswith("punto_acceso") for n in nombres),
                    f"{id_paquete}: el grupo no incluye ningun punto de acceso",
                )

                # Y las direcciones del grupo tienen que ser las mismas que usa la regla.
                del_grupo = {m["ip"] for m in grupo["miembros"]}
                de_la_regla = set(self._reglas(id_paquete)["controller_a_management"]["destino_direcciones"])
                self.assertEqual(
                    del_grupo, de_la_regla,
                    f"{id_paquete}: el grupo de vlans.yaml y el destino de la regla no coinciden. "
                    f"Si divergen, la regla protege un conjunto distinto del que el as-built documenta.",
                )

    def test_una_excepcion_hacia_trusted_no_abre_alcance_a_gestion(self):
        """El escenario que hace peligrosa la version anterior.

        En S y M, lo que de hecho impedia a Controller llegar a las interfaces de gestion era
        `controller_a_trusted: denegar`. Si alguien anade una excepcion legitima de Controller hacia
        Trusted -por ejemplo para un servicio nuevo-, con el modelo viejo abriria de paso el alcance
        a la pasarela y a los switches, sin tocar ninguna regla que mencione Management.

        Con `grupo_gestion`, la denegacion es explicita y sobrevive a esa excepcion.
        """
        for id_paquete in ("S", "M"):
            with self.subTest(paquete=id_paquete):
                reglas = self._reglas(id_paquete)
                gestion = reglas["controller_a_management"]

                # La regla no depende de `controller_a_trusted` para existir ni para tener destino.
                self.assertEqual(gestion["accion"], "denegar")
                self.assertTrue(gestion.get("destino_direcciones"))

                # Y su destino son direcciones, no el nombre del segmento Trusted: relajar
                # `controller_a_trusted` no las alcanza.
                self.assertNotEqual(gestion.get("destino"), "Trusted")
                trusted = reglas["controller_a_trusted"]
                self.assertNotEqual(
                    gestion.get("destino_direcciones"), trusted.get("destino_direcciones"),
                    "La proteccion de gestion no puede ser un efecto lateral de la regla de Trusted",
                )

    def test_ninguna_regla_permite_controller_hacia_management(self):
        """No basta con que exista la regla de denegacion: nada puede permitirlo por otra via."""
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                for regla in self._reglas(id_paquete).values():
                    if regla.get("origen") != "Controller":
                        continue
                    destino = regla.get("destino")
                    destinos = destino if isinstance(destino, list) else [destino]
                    if "Management" in destinos:
                        self.assertEqual(
                            regla["accion"], "denegar",
                            f"{id_paquete}: la regla '{regla['id']}' permite Controller -> Management",
                        )


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
