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

    def _entrada_admin(self, id_paquete: str) -> dict:
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
        return {r["id"]: r for r in datos["reglas_entrada"]}["entrada_admin_pasarela"]

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
                for esperado in ("switch_principal", "interfaz_fuera_de_banda"):
                    self.assertIn(esperado, nombres, f"{id_paquete}: falta {esperado} en el grupo")
                self.assertTrue(
                    any(n.startswith("punto_acceso") for n in nombres),
                    f"{id_paquete}: el grupo no incluye ningun punto de acceso",
                )
                # La pasarela ya no es un miembro suelto: es uno por VLAN presente, porque tiene
                # una interfaz en cada red que sirve y todas responden a la misma administracion.
                self.assertTrue(
                    any(n.startswith("pasarela_vlan_") for n in nombres),
                    f"{id_paquete}: el grupo no incluye ninguna interfaz de la pasarela",
                )

                # ENTRE LAS DOS REGLAS tienen que cubrir el grupo entero.
                #
                # Ya no basta con comparar el grupo contra la regla de reenvio: las interfaces de la
                # pasarela no se reenvian, terminan en el router, y las cubre la regla de entrada.
                # Lo que sigue siendo cierto, y es lo que importa, es que nada del grupo puede
                # quedarse sin regla. Si algo se cae de las dos listas, la regla protege un conjunto
                # distinto del que el as-built documenta.
                del_grupo = {m["ip"] for m in grupo["miembros"]}
                por_reenvio = set(self._reglas(id_paquete)["controller_a_management"]["destino_direcciones"])
                por_entrada = set(self._entrada_admin(id_paquete)["destino_direcciones"])
                self.assertEqual(
                    del_grupo - (por_reenvio | por_entrada), set(),
                    f"{id_paquete}: hay miembros de `grupo_gestion` que ninguna regla cubre, ni por "
                    f"reenvio ni por entrada.",
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


class LaPasarelaTieneUnaInterfazEnCadaVlan(unittest.TestCase):
    """El caso que hacia aparente la proteccion del acceso administrativo.

    `grupo_gestion` enumeraba cinco interfaces, todas en la VLAN receptora. Pero la pasarela tiene
    una interfaz en CADA VLAN que sirve, y todas responden a la misma administracion. Denegar
    `10.x.10.1` no impedia alcanzar `10.x.40.1`, que desde el controlador es literalmente su propia
    puerta de enlace. La regla cubria una direccion del router y dejaba abiertas las demas.
    """

    def test_el_grupo_contiene_la_puerta_de_enlace_de_cada_vlan_presente(self):
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                presentes = [v for v in datos["vlans"] if v.get("presente")]
                del_grupo = {m["ip"] for m in datos["grupo_gestion"]["miembros"]}

                faltan = [v["gateway"] for v in presentes if v["gateway"] not in del_grupo]
                self.assertEqual(
                    faltan, [],
                    f"{id_paquete}: `grupo_gestion` no cubre estas interfaces de la pasarela: "
                    f"{faltan}. Cada una es la misma administracion vista desde otra red.",
                )

    def test_cada_interfaz_de_pasarela_esta_marcada_con_su_rol(self):
        """Sin el rol, nadie sabe por que hay cinco direcciones que terminan en .1."""
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = renderizar_vlans(id_paquete)
                presentes = {v["id"] for v in datos["vlans"] if v.get("presente")}
                de_pasarela = {
                    m["vlan"] for m in datos["grupo_gestion"]["miembros"]
                    if m.get("rol") == "interfaz_de_pasarela"
                }
                self.assertEqual(
                    de_pasarela, presentes,
                    f"{id_paquete}: las interfaces de pasarela marcadas no coinciden con las VLAN "
                    f"presentes",
                )


class ReglasDeEntradaDeLaPasarela(unittest.TestCase):
    """Reenvio y entrada son rutas distintas. Una regla en la ruta equivocada no protege.

    El trafico dirigido a la pasarela no se reenvia: termina en ella y se filtra en otra ruta, que
    las reglas entre VLAN no tocan. UniFi, Omada y MikroTik se comportan asi. Una regla de reenvio
    con destino la IP de la pasarela no bloquea nada.
    """

    def _entrada(self, id_paquete: str) -> dict:
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
        return datos

    def test_existe_una_seccion_de_reglas_de_entrada_separada(self):
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = self._entrada(id_paquete)
                self.assertIn(
                    "reglas_entrada", datos,
                    f"{id_paquete}: no hay seccion de reglas de entrada. Las reglas entre VLAN no "
                    f"cubren el trafico dirigido a la pasarela misma.",
                )
                self.assertEqual(datos.get("politica_entrada_por_defecto"), "denegar")

    def test_se_deniega_la_administracion_desde_controller_iot_camera_y_guest(self):
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = self._entrada(id_paquete)
                reglas = {r["id"]: r for r in datos["reglas_entrada"]}
                self.assertIn("entrada_admin_pasarela", reglas)

                regla = reglas["entrada_admin_pasarela"]
                self.assertEqual(regla["accion"], "denegar")
                self.assertEqual(regla["ruta"], "entrada")

                denegados = set(regla["origenes_denegados"])
                esperados = {"Controller", "IoT", "Camera"}
                if 60 in validar.cargar_paquete(id_paquete)["vlans"]["presentes"]:
                    esperados.add("Guest")
                self.assertTrue(
                    esperados <= denegados,
                    f"{id_paquete}: faltan origenes denegados: {esperados - denegados}",
                )

    def test_la_regla_de_entrada_cubre_TODAS_las_interfaces_de_la_pasarela(self):
        """Probar solo una direccion es exactamente el error que esto corrige."""
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = self._entrada(id_paquete)
                regla = {r["id"]: r for r in datos["reglas_entrada"]}["entrada_admin_pasarela"]
                cubiertas = set(regla["destino_direcciones"])

                vlans = renderizar_vlans(id_paquete)["vlans"]
                gateways = {v["gateway"] for v in vlans if v.get("presente")}
                self.assertEqual(
                    gateways - cubiertas, set(),
                    f"{id_paquete}: la regla de entrada deja fuera {gateways - cubiertas}",
                )

    def test_la_puerta_de_enlace_del_propio_controlador_esta_cubierta(self):
        """El caso concreto: desde Controller, la administracion del router esta en su gateway."""
        for id_paquete in ("S", "M", "L", "XL"):
            with self.subTest(paquete=id_paquete):
                datos = self._entrada(id_paquete)
                regla = {r["id"]: r for r in datos["reglas_entrada"]}["entrada_admin_pasarela"]
                octeto = yaml.safe_load(DEMO.read_text(encoding="utf-8"))["red"]["octeto"]
                self.assertIn(
                    f"10.{octeto}.40.1", regla["destino_direcciones"],
                    f"{id_paquete}: la puerta de enlace del propio controlador no esta cubierta",
                )

    def test_dns_y_dhcp_siguen_permitidos_y_declarados_aparte(self):
        """Bloquearlos por error deja la instalacion sin resolver nombres."""
        datos = self._entrada("M")
        reglas = {r["id"]: r for r in datos["reglas_entrada"]}
        self.assertIn("entrada_dns_dhcp", reglas)
        self.assertEqual(reglas["entrada_dns_dhcp"]["accion"], "permitir")
        # Camera no pide DNS: su segmento no tiene salida.
        self.assertNotIn("Camera", reglas["entrada_dns_dhcp"]["origenes_permitidos"])


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
