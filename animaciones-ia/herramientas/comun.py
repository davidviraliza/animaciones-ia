"""Rutas y ayudas compartidas. Solo biblioteca estándar."""
import json, os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
_base = os.environ.get('ANIMACIONES_IA_DATOS') or os.path.join(os.environ.get('LOCALAPPDATA') or str(Path.home() / '.local' / 'share'), 'animaciones-ia')
DATOS = Path(_base)
ENV = DATOS / 'env'
PY_ENV = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
MODELOS = DATOS / 'modelos'
# modelos que se bajan con descargar.py (HTTP directo, con progreso y reintento)
WHISPER = {'large-v3-turbo': 'mobiuslabsgmbh/faster-whisper-large-v3-turbo', 'medium': 'Systran/faster-whisper-medium',
           'small': 'Systran/faster-whisper-small'}
WHISPER_ARCHIVOS = ['config.json', 'preprocessor_config.json', 'model.bin', 'tokenizer.json', 'vocabulary.*']
CHATTERBOX = ('ResembleAI/chatterbox', ['ve.pt', 't3_mtl23ls_v2.safetensors', 's3gen.pt', 'grapheme_mtl_merged_expanded_v1.json',
                                        'conds.pt', 'Cangjie5_TC.json'])
PIPER_VOZ = ('rhasspy/piper-voices', 'es/es_MX/claude/high/', ['es_MX-claude-high.onnx', 'es_MX-claude-high.onnx.json', 'MODEL_CARD'])


def en_entorno():
    return Path(sys.prefix).resolve() == ENV.resolve()


def preparar_modelos():
    """Los modelos (voz y transcripción) se guardan en DATOS/modelos, no en la carpeta del usuario."""
    MODELOS.mkdir(parents=True, exist_ok=True)
    os.environ['HF_HOME'] = str(MODELOS)
    os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
    os.environ.setdefault('HF_HUB_DISABLE_XET', '1')  # el modo xet se ha quedado quieto sin avisar; HTTP normal
    os.environ.setdefault('HF_HUB_OFFLINE', '1')  # lo necesario ya se bajó con descargar.py


def hay(prog):
    return shutil.which(prog) is not None


def correr(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', **kw)


def duracion(archivo):
    r = correr(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(archivo)])
    return float(r.stdout.strip() or 0)


def norm(w):
    w = unicodedata.normalize('NFKD', w.lower())
    w = ''.join(c for c in w if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9ñ]', '', w)


def leer_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def escribir_json(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')


def frases_de(guion):
    """Acepta {"frases": [...]} o una lista de {"id", "texto"}."""
    g = leer_json(guion)
    return g['frases'] if isinstance(g, dict) else g
