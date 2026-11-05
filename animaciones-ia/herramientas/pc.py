"""revisar: qué hay en la PC (solo mira). instalar: entorno de Python del plugin.
Base (siempre): faster-whisper (transcribir), yt-dlp (bajar la referencia para estudiarla) y Piper (voz B, sin tarjeta de video).
--clon: además torch con CUDA y Chatterbox (voz A, tu voz clonada; NVIDIA de 6 GB o más)."""
import argparse, platform, shutil, subprocess, sys, time
from comun import CHATTERBOX, DATOS, ENV, MODELOS, PIPER_VOZ, PY_ENV, WHISPER, WHISPER_ARCHIVOS, correr, escribir_json, hay

BASE = ['faster-whisper==1.2.1', 'piper-tts==1.8.0', 'yt-dlp', 'numpy<2', 'scipy', 'soundfile', 'num2words==0.5.14']
TORCH = ['torch==2.6.0', 'torchaudio==2.6.0']
CLON = ['chatterbox-tts==0.1.7']
PIP = ['--disable-pip-version-check', '--timeout', '60', '--retries', '5', '--progress-bar', 'on']


def gpu():
    if not hay('nvidia-smi'):
        return None
    r = correr(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'])
    if r.returncode != 0 or not r.stdout.strip():
        return None
    nombre, mem = [x.strip() for x in r.stdout.strip().splitlines()[0].split(',')]
    return {'nombre': nombre, 'vram_gb': round(int(mem) / 1024, 1)}


def version(cmd):
    try:
        r = correr(cmd)
        return (r.stdout or r.stderr).strip().splitlines()[0] if r.returncode == 0 else None
    except (OSError, IndexError):
        return None


def revisar(_):
    filas, falta = [], []
    node = version(['node', '--version'])
    ok_node = bool(node) and int(node.lstrip('v').split('.')[0]) >= 18
    filas.append(('Node.js (para Remotion)', node or 'no está', ok_node))
    if not ok_node:
        falta.append('Node.js LTS:  winget install -e --id OpenJS.NodeJS.LTS   (Windows te pedirá permiso una vez: es el instalador oficial)')
    npm = version(['npm.cmd' if sys.platform == 'win32' else 'npm', '--version'])
    filas.append(('npm (viene con Node)', npm or 'no está', bool(npm)))
    ff = version(['ffmpeg', '-version'])
    filas.append(('ffmpeg (cortar y mezclar audio/video)', (ff or 'no está')[:40], bool(ff) and hay('ffprobe')))
    if not ff:
        falta.append('ffmpeg:  winget install -e --id Gyan.FFmpeg   (sin permiso de administrador)')
    v = sys.version_info
    ok_py = (3, 10) <= v[:2] <= (3, 12)
    filas.append(('Python 3.10–3.12 (voz y transcripción)', platform.python_version(), ok_py))
    if not ok_py:
        falta.append('Python 3.11:  winget install -e --id Python.Python.3.11 --scope user   (sin permiso de administrador)')
    g = gpu()
    filas.append(('Tarjeta NVIDIA', f"{g['nombre']} · {g['vram_gb']} GB" if g else 'no hay: usarás la voz B (Piper), que no la necesita', True))
    libre = shutil.disk_usage(DATOS.anchor if DATOS.anchor else '.').free / 2**30
    need = 12 if g else 5
    filas.append((f'Espacio libre en {DATOS.anchor} (se ocupan ~{need} GB)', f'{libre:.0f} GB', libre > need))
    if libre <= need:
        falta.append(f'Libera espacio en {DATOS.anchor}: los modelos ocupan ~{need} GB')
    base_ok = PY_ENV.exists() and correr([str(PY_ENV), '-c', 'import faster_whisper, piper, yt_dlp, num2words']).returncode == 0
    filas.append(('Entorno del plugin (transcripción, descargas, voz B)', str(ENV) if base_ok else 'no está todavía', base_ok))
    if not base_ok and ok_py:
        falta.append('Entorno del plugin:  python ia.py instalar' + (' --clon   (o sin --clon si no quieres clonar tu voz)' if g and g['vram_gb'] >= 5.5 else ''))
    clon_ok = PY_ENV.exists() and correr([str(PY_ENV), '-c', 'import torch, chatterbox; assert torch.cuda.is_available()']).returncode == 0
    if g and g['vram_gb'] >= 5.5:
        filas.append(('Voz A: tu voz clonada (Chatterbox)', 'lista' if clon_ok else 'sin instalar (opcional: python ia.py instalar --clon)', True))
    else:
        filas.append(('Voz A: tu voz clonada (Chatterbox)', 'tu tarjeta no alcanza (pide NVIDIA de 6 GB): usa la voz B', True))
    filas.append(('winget (instalador de Windows)', 'sí' if hay('winget') else 'no está', hay('winget') or sys.platform != 'win32'))
    print('\nREVISIÓN DE TU PC\n')
    for n, val, ok in filas:
        print(f"  {'OK ' if ok else 'FALTA'}  {n}: {val}")
    print('\nQUÉ FALTA' if falta else '\nTodo listo.')
    for f in falta:
        print('  - ' + f)
    escribir_json(DATOS / 'revision.json', {'filas': [{'que': n, 'valor': val, 'ok': ok} for n, val, ok in filas], 'falta': falta, 'gpu': g})
    return 0 if not falta else 1


def pip(args, que):
    print(f'  {que}: pip install ' + ' '.join(args), flush=True)
    t = time.time()
    r = subprocess.run([str(PY_ENV), '-m', 'pip', 'install', *PIP, *args])
    if r.returncode != 0:
        raise SystemExit(f'Falló la instalación de {que}. Vuelve a correr el mismo comando: lo que ya se bajó no se repite.')
    print(f'  {que}: listo en {time.time() - t:.0f} s', flush=True)


def instalar(resto):
    import descargar
    a = argparse.ArgumentParser(prog='ia.py instalar')
    a.add_argument('--clon', action='store_true', help='también Chatterbox para clonar tu voz (NVIDIA de 6 GB o más)')
    a.add_argument('--whisper', default='large-v3-turbo', choices=list(WHISPER))
    o = a.parse_args(resto)
    if not (3, 10) <= sys.version_info[:2] <= (3, 12):
        print(f'Este Python es {platform.python_version()}; ocupo 3.10, 3.11 o 3.12. Instala:  winget install -e --id Python.Python.3.11 --scope user'); return 2
    g = gpu()
    if o.clon and not g:
        print('Para clonar tu voz (opción A) ocupas tarjeta NVIDIA. Instalo solo la base (voz B).'); o.clon = False
    pasos = 4 + (3 if o.clon else 0); n = 0
    t0 = time.time()
    DATOS.mkdir(parents=True, exist_ok=True)

    def paso(txt):
        nonlocal n
        n += 1
        print(f'\n{n}/{pasos} {txt}', flush=True)
    paso(f'Entorno de Python en {ENV}')
    if not PY_ENV.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(ENV)], check=True)
    if o.clon:
        paso('torch para tarjeta NVIDIA (CUDA 12.4): es la descarga grande, ~2.5 GB, 5–15 min')
        pip([*TORCH, '--index-url', 'https://download.pytorch.org/whl/cu124'], 'torch')
        paso('Chatterbox (clonar tu voz) y sus piezas, ~1 GB')
        pip(CLON, 'Chatterbox')
    paso('Transcripción (faster-whisper), descargas (yt-dlp) y voz B (Piper), ~200 MB')
    pip(BASE, 'base')
    paso(f'Modelo de transcripción whisper {o.whisper} (~1.6 GB, con progreso; si se atora, reintenta solo)')
    descargar.repo(WHISPER[o.whisper], MODELOS / 'whisper' / o.whisper, patrones=WHISPER_ARCHIVOS)
    paso('Voz B: Piper es_MX-claude-high (~60 MB)')
    for f in PIPER_VOZ[2]:
        descargar.archivo(f'{descargar.HF}/{PIPER_VOZ[0]}/resolve/main/{PIPER_VOZ[1]}{f}', DATOS / 'piper' / f)
    if o.clon:
        paso('Modelo de Chatterbox (~3 GB, con progreso; si se atora, reintenta solo)')
        descargar.repo(CHATTERBOX[0], MODELOS / 'chatterbox', CHATTERBOX[1])
    prueba = 'import faster_whisper, piper, yt_dlp' + ('; import torch, chatterbox; print(torch.__version__, torch.cuda.is_available())' if o.clon else '; print("base ok")')
    r = correr([str(PY_ENV), '-c', prueba])
    print(r.stdout.strip() or r.stderr[-800:])
    escribir_json(DATOS / 'instalado.json', {'clon': o.clon, 'gpu': g, 'prueba': r.stdout.strip(), 'minutos': round((time.time() - t0) / 60, 1)})
    print(f'\nListo en {(time.time() - t0) / 60:.1f} min.' if r.returncode == 0 else '\nAlgo no quedó: lee el error de arriba.')
    return r.returncode


def main(cmd, resto):
    return revisar(resto) if cmd == 'revisar' else instalar(resto)
