"""Transcripción local con faster-whisper (MIT), en el procesador (int8) para no pelear la tarjeta con la voz.
También compara lo que se oye contra el guion (error por palabra) y saca el tiempo de cada palabra del guion."""
import re, unicodedata
from difflib import SequenceMatcher
from comun import MODELOS, WHISPER, WHISPER_ARCHIVOS, preparar_modelos

_m = {}


def modelo(nombre='large-v3-turbo'):
    if nombre not in _m:
        preparar_modelos()
        import descargar
        from faster_whisper import WhisperModel
        dest = MODELOS / 'whisper' / nombre
        if not descargar.listo(dest):
            print(f'Bajando whisper {nombre} (una sola vez: turbo ~1.6 GB, medium ~1.5 GB, small ~0.5 GB) …', flush=True)
            descargar.repo(WHISPER[nombre], dest, patrones=WHISPER_ARCHIVOS)
        print(f'Cargando whisper {nombre} …', flush=True)
        _m[nombre] = WhisperModel(str(dest), device='cpu', compute_type='int8')
    return _m[nombre]


def transcribir(audio, nombre='large-v3-turbo', idioma='es'):
    """audio = ruta o arreglo float32 a 16 kHz. Sin pista del guion: así el error medido es real."""
    segs, info = modelo(nombre).transcribe(audio if hasattr(audio, 'shape') else str(audio), language=idioma, word_timestamps=True,
                                           beam_size=5, vad_filter=False)
    segs = list(segs)
    return [{'ini': round(s.start, 2), 'fin': round(s.end, 2), 'texto': s.text.strip(),
             'palabras': [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for w in s.words]} for s in segs], info.language


# ---------- comparar contra el guion ----------
def _numeros(texto):
    from num2words import num2words

    def cambiar(m):
        crudo = m.group(0)
        n = int(re.sub(r'[^\d]', '', crudo))
        return ' ' + num2words(n, lang='es') + ' '
    return re.sub(r'\d[\d., ]*\d|\d', cambiar, texto)


def norm(texto):
    """Palabras comparables: números en letra, sin acentos ni signos, en minúsculas."""
    texto = _numeros(texto.lower())
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.findall(r'[a-zñ]+', texto)


def errores(ref, hip):
    """Distancia de edición por palabra (cambiadas + sobrantes + faltantes)."""
    d = list(range(len(hip) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hip, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
    return d[len(hip)]


def tiempos(texto, oidas, desfase=0.0):
    """A cada palabra del guion le da su inicio y fin con las marcas de whisper (oidas = [{'w','s','e'}]).
    Las palabras escritas son las del guion: los subtítulos nunca muestran errores de transcripción."""
    toks = []
    for p in oidas:
        partes = norm(p['w'])
        if not partes:
            continue
        paso = (p['e'] - p['s']) / len(partes)
        toks += [(x, p['s'] + k * paso, p['s'] + (k + 1) * paso) for k, x in enumerate(partes)]
    guion = texto.split()
    ref = [(norm(w) or [''])[0] for w in guion]
    hip = [t[0] for t in toks]
    res = [None] * len(guion)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, ref, hip, autojunk=False).get_opcodes():
        if tag in ('equal', 'replace'):
            for k in range(min(i2 - i1, j2 - j1)):
                res[i1 + k] = toks[j1 + k][1:]
    fin_total = toks[-1][2] if toks else 0.3 * len(guion)
    for i in range(len(res)):
        if res[i] is None:
            antes = next((res[k][1] for k in range(i - 1, -1, -1) if res[k]), 0.0)
            despues = next((res[k][0] for k in range(i + 1, len(res)) if res[k]), fin_total)
            res[i] = (antes, max(antes + 0.05, despues))
    return [{'w': w, 's': round(desfase + s, 3), 'e': round(desfase + max(e, s + 0.05), 3)} for w, (s, e) in zip(guion, res)]
