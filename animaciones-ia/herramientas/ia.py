"""Punto de entrada único de las herramientas del plugin Animaciones con IA.

    python ia.py revisar                       qué tiene y qué le falta a tu PC (solo mira, no instala)
    python ia.py instalar [--clon]             entorno de Python del plugin: transcripción, descargas y voz Piper (B);
                                               con --clon, además Chatterbox para clonar tu voz (A, NVIDIA de 6 GB o más)
    python ia.py proyecto <carpeta>            copia la plantilla de video a <carpeta>/video e instala Remotion
    python ia.py analizar <enlace|video> <carpeta>   baja (solo para estudiar) y analiza un video de referencia
    python ia.py voz <revisar-muestra|narrar> ...    voz A (tu voz clonada, Chatterbox) o B (voz ya hecha, Piper)
    python ia.py musica --voz F --salida F     música original (sintetizada nota por nota) con entrada, desarrollo, tensión y cierre
    python ia.py acabado ...                   mezcla voz + música (18 dB debajo) a -14 LUFS y la pega al video
    python ia.py hoja ...                      hoja de contacto: un cuadro por frase (del video o de cuadros fijos de Remotion)
    python ia.py medir ...                     mide el video terminado: LUFS, picos, duración y transcripción contra el guion

Cada comando corre con un TOPE de tiempo y avisa que sigue vivo si pasa medio minuto sin escribir nada.
Si llega al tope, se detiene solo y lo dice (nada se queda dando vueltas por horas). Cambia el tope con la variable IA_TOPE_S.
Se corre con cualquier Python 3.10–3.12; lo que ocupa modelos se pasa solo al entorno del plugin.
Datos y modelos: %LOCALAPPDATA%\\animaciones-ia (o la carpeta de la variable ANIMACIONES_IA_DATOS).
"""
import os, subprocess, sys, threading, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from comun import PY_ENV, en_entorno  # noqa: E402

LIGEROS = {'revisar', 'instalar', 'proyecto'}  # solo biblioteca estándar: corren con el Python del sistema
MODULOS = {'revisar': 'pc', 'instalar': 'pc', 'proyecto': 'proyecto', 'analizar': 'analizar', 'voz': 'voz',
           'musica': 'musica', 'acabado': 'acabado', 'hoja': 'hoja', 'medir': 'medir'}
# tope en segundos: lo normal tarda mucho menos; esto solo evita procesos colgados
TOPES = {'revisar': 120, 'instalar': 3600, 'proyecto': 900, 'analizar': 1800, 'voz': 3600,
         'musica': 300, 'acabado': 900, 'hoja': 1500, 'medir': 1200}
AVISO_S = 30


def _matar(p):
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(p.pid)], capture_output=True)
    else:
        p.kill()


def vigilado(cmd, args):
    """Corre el comando en un proceso hijo: pasa su salida tal cual, avisa si lleva rato callado y lo detiene al tope."""
    tope = float(os.environ.get('IA_TOPE_S') or TOPES.get(cmd, 1800))
    py = sys.executable if (cmd in LIGEROS or en_entorno()) else str(PY_ENV)
    env = dict(os.environ, IA_HIJO='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
    t0 = time.time(); ultimo = [t0]
    p = subprocess.Popen([py, str(AQUI / 'ia.py'), cmd, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, bufsize=0)

    def pasar():
        while True:
            b = p.stdout.read1(4096) if hasattr(p.stdout, 'read1') else p.stdout.read(1)
            if not b:
                break
            ultimo[0] = time.time()
            sys.stdout.buffer.write(b); sys.stdout.flush()
    hilo = threading.Thread(target=pasar, daemon=True); hilo.start()
    while p.poll() is None:
        time.sleep(1)
        ahora = time.time()
        if ahora - t0 > tope:
            _matar(p)
            print(f'\nALTO: «{cmd}» llegó a su tope de {tope / 60:.0f} min y lo detuve para que no se quede dando vueltas. '
                  'Lo normal es que tarde mucho menos: algo se atoró. Lee las últimas líneas de arriba para ver dónde.', flush=True)
            hilo.join(5)
            return 124
        if ahora - ultimo[0] >= AVISO_S:
            print(f'  … sigue trabajando ({ahora - t0:.0f} s de un tope de {tope / 60:.0f} min)', flush=True)
            ultimo[0] = ahora
    hilo.join(5)
    return p.returncode


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'ayuda'):
        print(__doc__); return 0
    cmd, resto = sys.argv[1], sys.argv[2:]
    mod = MODULOS.get(cmd)
    if not mod:
        print(f'No conozco «{cmd}».'); print(__doc__); return 2
    if cmd not in LIGEROS and not en_entorno() and not PY_ENV.exists():
        print(f'Falta el entorno del plugin ({PY_ENV}). Corre primero: /animaciones-ia:preparar (o python ia.py instalar)'); return 2
    if not os.environ.get('IA_HIJO') and '-h' not in resto and '--help' not in resto:
        return vigilado(cmd, resto)
    m = __import__(mod)
    return m.main(cmd, resto) or 0


if __name__ == '__main__':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    try:
        sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.exit(main())
