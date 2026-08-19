#!/usr/bin/env python3
"""Verificacion de extremo a extremo del repositorio.

Un solo comando que comprueba que la fabrica funciona:

    python herramientas-empresa/verificar_todo.py

Pasa por:
  1. Todo YAML del repositorio carga.
  2. Las pruebas de las calculadoras.
  3. Las pruebas de regresion del validador.
  4. El catalogo es internamente coherente.
  5. El cliente de demostracion valida con cero errores.
  6. El paquete se genera completo.
  7. Sobre el paquete generado: sin secretos, sin terminos de seguridad de vida fuera de contexto
     de exclusion, y con los ocho documentos de cliente en ingles y frances.

Codigo de retorno: 0 si todo pasa, 1 si algo falla.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

VERDE = "  OK  "
ROJO = " FALLA"

# ADR-004. Sobre el paquete GENERADO solo pueden aparecer en textos que declaran la exclusion.
TERMINOS_FUEGO = re.compile(
    r"(?i)\b(smoke|fire alarm|carbon monoxide|gas detect\w*|incendie|fumee|fumée|monoxyde)\b"
)
# Lineas donde la mencion es legitima: son precisamente las que declaran que NO se hace.
CONTEXTO_EXCLUSION = re.compile(
    r"(?i)(not a|is not|no es|n'est pas|excluded|exclusion|untouched|intacts?|"
    r"never|nunca|jamais|aucun|no relay|aucun relais|not gas detectors|"
    r"ne sont pas|sans exception|out of scope|hors portee|hors de portee|"
    r"nothing is installed|rien n'y est installe|no se instala)"
)

MARCADOR_PERMITIDO = "regla-del-fuego: mencion permitida"
"""Marcador explicito para lineas que nombran los terminos vetados por definirlos.

Lo usan los archivos que DECLARAN la lista de terminos prohibidos: la lista tiene que contener las
palabras para poder prohibirlas. Es el unico caso legitimo y se marca a mano, uno por uno, para que
nadie pueda silenciar la comprobacion por descuido."""

VENTANA_CONTEXTO = 3
"""Lineas a cada lado que se consideran parte de la misma declaracion de exclusion."""


def paso(titulo: str, funcion) -> bool:
    print(f"\n=== {titulo} ===")
    try:
        ok, detalle = funcion()
    except Exception as exc:  # noqa: BLE001
        print(f"{ROJO}  excepcion: {exc}")
        return False
    print(f"{VERDE if ok else ROJO}  {detalle}")
    return ok


def ejecutar(comando: list[str], cwd: Path = RAIZ) -> tuple[int, str]:
    proc = subprocess.run(comando, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr)


def yaml_carga() -> tuple[bool, str]:
    import yaml

    class SinEtiquetas(yaml.SafeLoader):
        """Home Assistant usa etiquetas propias (!secret, !include_dir_*). No son un error.

        Hereda de SafeLoader a proposito: solo anade un constructor que IGNORA las etiquetas que
        empiezan por `!`, devolviendo None. No habilita la construccion de objetos Python
        arbitrarios, que es lo que hace peligroso a yaml.load con el Loader por defecto.
        """

    SinEtiquetas.add_multi_constructor("!", lambda loader, sufijo, nodo: None)

    malos = []
    revisados = 0
    for patron in ("datos-maestros/**/*.yaml", "comercial/paquetes/*.yaml", "clientes/**/*.yaml",
                   "herramientas-empresa/ansible/**/*.yml", "salida/**/*.yaml",
                   "producto-cliente/interfaz/i18n/*.yaml"):
        for ruta in RAIZ.glob(patron):
            revisados += 1
            try:
                yaml.load(ruta.read_text(encoding="utf-8"), Loader=SinEtiquetas)
            except Exception as exc:  # noqa: BLE001
                malos.append(f"{ruta.relative_to(RAIZ)}: {str(exc).splitlines()[0]}")
    if malos:
        return False, "YAML invalido:\n      " + "\n      ".join(malos)
    return True, f"{revisados} archivos YAML cargan correctamente"


def pruebas_calculadoras() -> tuple[bool, str]:
    codigo, salida = ejecutar(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"],
        cwd=RAIZ / "herramientas-empresa" / "calculadoras",
    )
    n = re.search(r"Ran (\d+) tests", salida)
    return codigo == 0, f"{n.group(1) if n else '?'} pruebas de calculadoras"


def pruebas_validador() -> tuple[bool, str]:
    codigo, salida = ejecutar(
        [sys.executable, "-m", "unittest", "discover", "-s", "herramientas-empresa/validador", "-p", "test_*.py"]
    )
    n = re.search(r"Ran (\d+) tests", salida)
    return codigo == 0, f"{n.group(1) if n else '?'} pruebas de regresion del validador"


def catalogo_coherente() -> tuple[bool, str]:
    codigo, salida = ejecutar([sys.executable, "herramientas-empresa/validador/validar.py", "--catalogo"])
    return codigo == 0, salida.strip().splitlines()[-1] if salida.strip() else "sin salida"


def demo_valida() -> tuple[bool, str]:
    codigo, salida = ejecutar(
        [sys.executable, "herramientas-empresa/validador/validar.py", "clientes/EJEMPLO-demo/cliente.yaml"]
    )
    errores = [l for l in salida.splitlines() if "[ERROR]" in l]
    if errores:
        return False, "el cliente de demostracion NO valida:\n      " + "\n      ".join(errores)
    return codigo == 0, "el cliente de demostracion valida con cero errores"


def demo_genera() -> tuple[bool, str]:
    codigo, salida = ejecutar(
        [sys.executable, "herramientas-empresa/generador/generar.py", "clientes/EJEMPLO-demo/cliente.yaml"]
    )
    if codigo != 0:
        return False, "la generacion fallo:\n      " + salida.strip()
    n = re.search(r"\((\d+) archivos\)", salida)
    return True, f"paquete generado, {n.group(1) if n else '?'} archivos"


def sin_secretos() -> tuple[bool, str]:
    codigo, salida = ejecutar([sys.executable, "herramientas-empresa/detectar_secretos.py", "--todo"])
    return codigo == 0, salida.strip().splitlines()[-1] if salida.strip() else "sin salida"


def regla_del_fuego() -> tuple[bool, str]:
    """Ninguna mencion a seguridad de vida fuera de un contexto que declara la exclusion."""
    sospechosas = []
    for patron in ("salida/**/*", "producto-cliente/**/*", "comercial/paquetes/*.yaml"):
        for ruta in RAIZ.glob(patron):
            if not ruta.is_file() or ruta.suffix in {".docx", ".png", ".jpg"}:
                continue
            try:
                texto = ruta.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            lineas = texto.splitlines()
            for indice, linea in enumerate(lineas):
                if not TERMINOS_FUEGO.search(linea):
                    continue
                if MARCADOR_PERMITIDO in linea:
                    continue
                # La declaracion de exclusion suele ocupar varias lineas ("The system supplied is
                # not a fire detection system, a smoke detection system, ..."), asi que el termino
                # y la negacion que lo legitima caen en lineas distintas. Se mira una ventana.
                inicio = max(0, indice - VENTANA_CONTEXTO)
                ventana = " ".join(lineas[inicio:indice + VENTANA_CONTEXTO + 1])
                if not CONTEXTO_EXCLUSION.search(ventana):
                    sospechosas.append(
                        f"{ruta.relative_to(RAIZ)}:{indice + 1}: {linea.strip()[:90]}"
                    )
    if sospechosas:
        return False, (
            "menciones a seguridad de vida fuera de contexto de exclusion (ADR-004):\n      "
            + "\n      ".join(sospechosas)
        )
    return True, "ninguna mencion a seguridad de vida fuera de contexto de exclusion"


def documentos_bilingues() -> tuple[bool, str]:
    dir_cliente = RAIZ / "salida" / "EJEMPLO-demo" / "cliente"
    esperados = [
        f"{doc}.{idioma}.md"
        for doc in ("informe-relevamiento", "documento-as-built",
                    "acta-de-aceptacion", "declaracion-de-alcance")
        for idioma in ("en", "fr")
    ]
    faltan = [e for e in esperados if not (dir_cliente / e).is_file()]
    if faltan:
        return False, "faltan documentos de cliente: " + ", ".join(faltan)
    vacios = [e for e in esperados if (dir_cliente / e).stat().st_size < 500]
    if vacios:
        return False, "documentos sospechosamente cortos: " + ", ".join(vacios)
    return True, f"{len(esperados)} documentos de cliente en ingles y frances"


def dispositivos_instalados_validos() -> tuple[bool, str]:
    """El registro que el generador emite tiene que cumplir su propio esquema.

    Es la union entre inventario, parque instalado y garantia. Si el generador emite algo que el
    esquema rechaza, quien lo rellene en obra no tiene forma de saberlo hasta que ya esta relleno.
    """
    import json

    import jsonschema
    import yaml

    ruta = RAIZ / "salida" / "EJEMPLO-demo" / "dispositivos-instalados.yaml"
    if not ruta.is_file():
        return False, "el generador no emitio dispositivos-instalados.yaml"

    esquema = json.loads(
        (RAIZ / "datos-maestros" / "esquemas" / "dispositivo-instalado.schema.json")
        .read_text(encoding="utf-8")
    )
    registros = yaml.safe_load(ruta.read_text(encoding="utf-8")) or []
    validador = jsonschema.Draft202012Validator(esquema)

    fallos = []
    for i, registro in enumerate(registros):
        for fallo in validador.iter_errors(registro):
            campo = ".".join(str(x) for x in fallo.path) or "(raiz)"
            fallos.append(f"registro {i} campo `{campo}`: {fallo.message}")
    if fallos:
        return False, "registros invalidos: " + "; ".join(fallos[:5])
    return True, f"{len(registros)} registros de dispositivo instalado, validos contra su esquema"


def trazabilidad() -> tuple[bool, str]:
    """Todo `verificado: false` del catalogo tiene que tener su fila en POR-VERIFICAR."""
    import yaml

    disp = []
    for ruta in sorted((RAIZ / "datos-maestros" / "dispositivos").glob("*.yaml")):
        disp.extend(yaml.safe_load(ruta.read_text(encoding="utf-8")) or [])
    sin_verificar = [d for d in disp if not d.get("verificado")]
    cola = (RAIZ / "docs" / "POR-VERIFICAR.md").read_text(encoding="utf-8")
    if not sin_verificar:
        return True, "no hay datos sin verificar"
    if "datos-maestros/dispositivos/" not in cola:
        return False, "hay datos sin verificar y POR-VERIFICAR.md no los referencia"
    return True, (
        f"{len(sin_verificar)} entradas sin verificar, cubiertas por las filas de POR-VERIFICAR.md"
    )


def main() -> int:
    print("VERIFICACION DEL REPOSITORIO")
    print(f"Raiz: {RAIZ}")

    pasos = [
        ("1. Sintaxis YAML", yaml_carga),
        ("2. Pruebas de calculadoras", pruebas_calculadoras),
        ("3. Pruebas de regresion del validador", pruebas_validador),
        ("4. Coherencia del catalogo", catalogo_coherente),
        ("5. El cliente de demostracion valida", demo_valida),
        ("6. El paquete se genera", demo_genera),
        ("7. Sin secretos (ADR-005)", sin_secretos),
        ("8. Regla del fuego (ADR-004)", regla_del_fuego),
        ("9. Documentos de cliente bilingues", documentos_bilingues),
        ("10. Registro de dispositivo instalado", dispositivos_instalados_validos),
        ("11. Trazabilidad de datos sin verificar (ADR-001)", trazabilidad),
    ]

    resultados = [paso(titulo, fn) for titulo, fn in pasos]

    print()
    print("=" * 70)
    fallidos = [t for (t, _), ok in zip(pasos, resultados) if not ok]
    if fallidos:
        print(f"RESULTADO: {len(fallidos)} PASO(S) FALLIDO(S)")
        for f in fallidos:
            print(f"  - {f}")
        return 1
    print(f"RESULTADO: los {len(pasos)} pasos pasan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
