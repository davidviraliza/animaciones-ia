"""Copia la plantilla de video a <carpeta>/video e instala Remotion ahí (npm install). No toca la plantilla del plugin."""
import argparse, shutil, subprocess, sys, time
from pathlib import Path
from comun import PLUGIN


def main(_cmd, resto):
    a = argparse.ArgumentParser(prog='ia.py proyecto')
    a.add_argument('carpeta', help='carpeta de tu video (se crea si no existe)')
    a.add_argument('--sin-npm', action='store_true', help='solo copia, no instala')
    o = a.parse_args(resto)
    raiz = Path(o.carpeta).resolve()
    dest = raiz / 'video'
    if dest.exists() and any(dest.iterdir()):
        print(f'{dest} ya existe: no la piso. Si quieres empezar de cero, bórrala tú o usa otra carpeta.')
    else:
        shutil.copytree(PLUGIN / 'plantilla', dest, ignore=shutil.ignore_patterns('node_modules', 'salida'))
        print(f'Plantilla copiada a {dest}')
    for d in ('referencia', 'voz', 'audio', 'entrega'):
        (raiz / d).mkdir(parents=True, exist_ok=True)
    if o.sin_npm or (dest / 'node_modules' / 'remotion').exists():
        return 0
    t0 = time.time()
    print('Instalando Remotion (npm install, 1–3 min la primera vez) …', flush=True)
    r = subprocess.run(['npm.cmd' if sys.platform == 'win32' else 'npm', 'install', '--no-audit', '--no-fund'], cwd=dest)
    print(f'npm install terminó en {time.time() - t0:.0f} s (código {r.returncode})')
    return r.returncode
