#!/usr/bin/env python3
"""Detector de secretos para el repositorio de la fabrica de despliegues.

Implementa la regla inviolable ADR-005: ninguna contrasena, clave o token entra al repositorio.
Se ejecuta como hook de pre-commit (via `.githooks/pre-commit`) sobre los archivos en el area de
preparacion, o sobre todo el arbol de trabajo con `--todo`.

Sin dependencias externas: solo biblioteca estandar, para que funcione en cualquier maquina de la
empresa sin instalar nada.

Uso:
    python herramientas/detectar_secretos.py archivo1 archivo2 ...
    python herramientas/detectar_secretos.py --todo
    python herramientas/detectar_secretos.py --preparados      # archivos en el indice de git

Codigo de retorno: 0 si esta limpio, 1 si encontro algo.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Marcadores de posicion permitidos. Un valor que coincida con alguno de estos no es un secreto:
# es exactamente lo que el repositorio debe contener en lugar de un secreto.
MARCADORES_PERMITIDOS = re.compile(
    r"""^(
        CAMBIAR-EN-COMISIONAMIENTO
        | CAMBIAR[-_A-Z]*
        | EN-EL-BAUL[-A-Z]*
        | VER-VAULTWARDEN
        | REDACTADO
        | PLACEHOLDER
        | XXX+
        | \{\{.*\}\}                 # expresion Jinja: el valor lo inyecta el generador
        | !vault.*
        | !secreto?\s+\S+           # referencia a secrets.yaml de Home Assistant
        | \{[A-Z0-9_]+\}             # sustitucion por variable de entorno (Frigate, docker)
        | \$\{[A-Za-z0-9_]+\}
        | \$[A-Z][A-Z0-9_]*
        | <[^>]+>                    # marcador angular del tipo <contrasena-del-cliente>
        | \$ANSIBLE_VAULT.*
        | \s*
        | null | ~ | ""|''
    )$""",
    re.VERBOSE | re.IGNORECASE,
)

# (nombre legible, expresion, grupo que contiene el valor a juzgar; None = coincidencia entera)
PATRONES = [
    (
        "clave privada en bloque PEM",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        None,
    ),
    (
        "clave privada de WireGuard",
        re.compile(r"(?i)\bPrivateKey\s*=\s*([A-Za-z0-9+/]{42,44}=)"),
        1,
    ),
    (
        "contrasena asignada en YAML o INI",
        re.compile(
            r"(?i)^\s*[-\w.]*(?:password|passwd|contrasena|mot_de_passe|secret|passphrase)"
            r"\s*[:=]\s*(?!#)(\S.*?)\s*(?:#.*)?$"
        ),
        1,
    ),
    (
        "token o clave de API",
        re.compile(
            r"(?i)^\s*[-\w.]*(?:api[_-]?key|apikey|auth[_-]?token|access[_-]?token|"
            r"bearer[_-]?token|client[_-]?secret|token)\s*[:=]\s*(?!#)(\S.*?)\s*(?:#.*)?$"
        ),
        1,
    ),
    (
        "token de GitHub",
        re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{30,})\b"),
        1,
    ),
    (
        "clave de AWS",
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        1,
    ),
    (
        "credencial embebida en URL",
        re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:([^/\s:@]{4,})@"),
        1,
    ),
    (
        "hash de contrasena de sistema",
        re.compile(r"(\$[0-9a-z]{1,3}\$(?:[./A-Za-z0-9=,]+\$)+[./A-Za-z0-9]{20,})"),
        1,
    ),
]

EXTENSIONES_BINARIAS = {
    ".docx", ".xlsx", ".pptx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip",
    ".gz", ".tar", ".7z", ".ico", ".woff", ".woff2", ".ttf", ".mp4", ".webp",
}

DIRECTORIOS_IGNORADOS = {".git", "referencia", "salida", "__pycache__", ".venv", "venv", "node_modules"}

# El propio detector contiene por fuerza los patrones que busca.
ARCHIVOS_EXENTOS = {"herramientas/detectar_secretos.py"}


def ruta_relativa(ruta: Path) -> str:
    """Ruta legible respecto a la raiz del repo; devuelve la absoluta si cae fuera de el."""
    try:
        return ruta.resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return ruta.as_posix()


def es_marcador(valor: str) -> bool:
    """True si el valor es un marcador de posicion aceptable en lugar de un secreto real."""
    limpio = valor.strip().strip("\"'").strip()
    if not limpio:
        return True
    return bool(MARCADORES_PERMITIDOS.match(limpio))


def revisar_archivo(ruta: Path) -> list[tuple[int, str, str]]:
    """Devuelve [(numero_de_linea, nombre_del_patron, fragmento)] de los hallazgos."""
    relativa = ruta_relativa(ruta)
    if relativa in ARCHIVOS_EXENTOS:
        return []
    if ruta.suffix.lower() in EXTENSIONES_BINARIAS:
        return []
    try:
        texto = ruta.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    hallazgos: list[tuple[int, str, str]] = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if "detectar-secretos: permitido" in linea:
            continue
        for nombre, patron, grupo in PATRONES:
            coincidencia = patron.search(linea)
            if not coincidencia:
                continue
            valor = coincidencia.group(grupo) if grupo else coincidencia.group(0)
            if grupo is not None and es_marcador(valor):
                continue
            fragmento = linea.strip()
            if len(fragmento) > 100:
                fragmento = fragmento[:97] + "..."
            hallazgos.append((numero, nombre, fragmento))
            break
    return hallazgos


def archivos_del_arbol() -> list[Path]:
    encontrados = []
    for ruta in RAIZ.rglob("*"):
        if not ruta.is_file():
            continue
        if any(parte in DIRECTORIOS_IGNORADOS for parte in ruta.parts):
            continue
        encontrados.append(ruta)
    return encontrados


def archivos_preparados() -> list[Path]:
    salida = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=RAIZ, capture_output=True, text=True, check=False,
    )
    rutas = []
    for linea in salida.stdout.splitlines():
        candidata = RAIZ / linea.strip()
        if candidata.is_file():
            rutas.append(candidata)
    return rutas


def main() -> int:
    analizador = argparse.ArgumentParser(description="Detecta secretos antes de que entren al repositorio.")
    analizador.add_argument("archivos", nargs="*", help="Archivos a revisar.")
    analizador.add_argument("--todo", action="store_true", help="Revisa todo el arbol de trabajo.")
    analizador.add_argument("--preparados", action="store_true", help="Revisa el area de preparacion de git.")
    args = analizador.parse_args()

    if args.todo:
        objetivos = archivos_del_arbol()
    elif args.preparados:
        objetivos = archivos_preparados()
    elif args.archivos:
        objetivos = [Path(a) if Path(a).is_absolute() else RAIZ / a for a in args.archivos]
    else:
        objetivos = archivos_preparados()

    total = 0
    for ruta in objetivos:
        if not ruta.is_file():
            continue
        for numero, nombre, fragmento in revisar_archivo(ruta):
            relativa = ruta_relativa(ruta)
            print(f"  {relativa}:{numero}  [{nombre}]")
            print(f"      {fragmento}")
            total += 1

    if total:
        print()
        print(f"SECRETOS DETECTADOS: {total}. El commit queda bloqueado (ADR-005).")
        print("Sustituye el valor por un marcador (CAMBIAR-EN-COMISIONAMIENTO), cifralo con")
        print("ansible-vault, o guardalo en el baul de credenciales del cliente.")
        print("Si es un falso positivo, anade el comentario  # detectar-secretos: permitido  en la linea.")
        return 1

    print(f"Sin secretos en {len(objetivos)} archivo(s) revisado(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
