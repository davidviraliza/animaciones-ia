"""Voz local y gratis, con control de calidad frase por frase (como en el tutorial).

    revisar-muestra  registra TU grabación (mi_voz.wav, 20–30 s) para clonarla. Exige --es-mi-voz (o --tengo-permiso).
    narrar           narra guion.json frase por frase:
                       --motor chatterbox  opción A: tu voz clonada (Chatterbox Multilingual, MIT; NVIDIA de 6 GB o más)
                       --motor piper       opción B: voz ya hecha en español de México, sin tarjeta de video (Piper es_MX-claude-high)
                     Cada frase se transcribe con faster-whisper; si una palabra no coincide con el guion se regenera
                     (máximo 3 intentos) y se queda la mejor. Se unen con pausas de 0.10 a 0.25 s.
                     Sale: narracion.wav, tiempos.json (cada palabra), calidad.json (% de error por palabra).
"""
import argparse, hashlib, subprocess, time, wave
from pathlib import Path
from comun import DATOS, CHATTERBOX, MODELOS, PIPER_VOZ, duracion, escribir_json, frases_de, leer_json, preparar_modelos

# silencio que se OYE entre frases (0.10–0.25 s): ya cuenta las orillas que deja recorte() (0.02 + 0.04 s)
PAUSA_NORMAL, PAUSA_LARGA, PAUSA_CORTA = 0.15, 0.22, 0.11
ORILLAS = 0.06
ESTILO = dict(exaggeration=0.55, cfg_weight=0.45, temperature=0.8)  # natural y conversacional
PIPER_VARIANTES = [dict(length_scale=1.0, noise_scale=0.667, noise_w_scale=0.8),
                   dict(length_scale=1.04, noise_scale=0.5, noise_w_scale=0.6),
                   dict(length_scale=0.97, noise_scale=0.75, noise_w_scale=0.9)]


def a_wav(src, dest, sr=24000, max_s=None):
    args = ['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-ac', '1', '-ar', str(sr)]
    if max_s:
        args += ['-t', str(max_s)]
    subprocess.run([*args, str(dest)], check=True)


def recorte(x, sr, umbral=-45.0, antes=0.02, despues=0.04):
    """Quita el silencio de las orillas con ventanas de 10 ms."""
    import numpy as np
    v = int(sr * 0.01); n = len(x) // v
    if n == 0:
        return x
    rms = np.sqrt(np.mean(x[:n * v].reshape(n, v) ** 2, axis=1) + 1e-12)
    voz = np.where(20 * np.log10(rms) > umbral)[0]
    if len(voz) == 0:
        return x
    a = max(0, voz[0] * v - int(antes * sr)); b = min(len(x), (voz[-1] + 1) * v + int(despues * sr))
    return x[a:b]


# ---------- la muestra de tu voz ----------
def revisar_muestra(o):
    if not (o.es_mi_voz or o.tengo_permiso):
        print('ALTO: solo se clona TU voz, o la de alguien que te dio permiso por escrito. Confirma que la grabación es tuya '
              'y vuelve a correr con --es-mi-voz (o con --tengo-permiso "nombre, cómo y cuándo te lo dio").'); return 2
    src = Path(o.muestra)
    if not src.exists():
        print(f'No encuentro {src}. Graba 20–30 s hablando normal y guárdalo en tu carpeta como mi_voz.wav.'); return 2
    dest = Path(o.salida); dest.parent.mkdir(parents=True, exist_ok=True)
    wav = dest.with_suffix('.wav')
    a_wav(src, wav, max_s=30)
    d = duracion(wav)
    if d < 10:
        print(f'La grabación dura {d:.1f} s: ocupo de 20 a 30 s hablando claro (mínimo 10).'); return 2
    import numpy as np, soundfile as sf
    x, sr = sf.read(str(wav), dtype='float32')
    pico = float(np.abs(x).max()); recortes = float(np.mean(np.abs(x) > 0.99))
    avisos = []
    if recortes > 0.001:
        avisos.append('la grabación satura (se oye «reventada»): grábala más bajito o más lejos del micrófono')
    if pico < 0.1:
        avisos.append('la grabación está muy bajita: acércate al micrófono')
    escribir_json(dest.with_suffix('.json'), {'audio': str(wav.resolve()), 'origen': 'clon', 'dur': round(d, 2),
                                             'declaracion': 'es mi voz' if o.es_mi_voz else f'con permiso: {o.tengo_permiso}',
                                             'fecha': time.strftime('%Y-%m-%d %H:%M')})
    print(f'Muestra registrada → {dest.with_suffix(".json")} ({d:.1f} s)' + ('' if 20 <= d <= 30 else ' · lo ideal son 20–30 s'))
    for a in avisos:
        print('  AVISO: ' + a)
    return 0


# ---------- motores ----------
class Chatterbox:
    nombre = 'Chatterbox Multilingual (Resemble AI, MIT)'

    def __init__(self, voz, cpu=False):
        preparar_modelos()
        import os
        os.environ.setdefault('TQDM_DISABLE', '1')  # sin la barra «Sampling» por cada frase: el avance lo dice cada intento
        import torch, descargar
        dest = MODELOS / 'chatterbox'
        if not descargar.listo(dest):
            print('Bajando Chatterbox (una sola vez, ~3 GB, con progreso) …', flush=True)
            descargar.repo(CHATTERBOX[0], dest, CHATTERBOX[1])
        cuda = torch.cuda.is_available() and not cpu
        if not cuda and not cpu:
            raise SystemExit('No veo una tarjeta NVIDIA con CUDA. Usa la opción B (--motor piper) o, si quieres esperar mucho, --cpu.')
        if cuda:
            vram = torch.cuda.get_device_properties(0).total_memory / 2**30
            if vram < 5.5:
                print(f'AVISO: tu tarjeta tiene {vram:.1f} GB; Chatterbox pide 6 GB. Si falla por memoria, usa la opción B.', flush=True)
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        t = time.time()
        print(f"Cargando Chatterbox en {'la tarjeta ' + torch.cuda.get_device_name(0) if cuda else 'el procesador (muy lento)'} …", flush=True)
        self.torch = torch
        self.tts = ChatterboxMultilingualTTS.from_local(dest, 'cuda' if cuda else 'cpu')
        self.sr = self.tts.sr
        self.voz = voz['audio']
        print(f'Chatterbox listo en {time.time() - t:.0f} s', flush=True)

    def decir(self, texto, intento, semilla):
        self.torch.manual_seed(semilla)
        w = self.tts.generate(texto, language_id='es', audio_prompt_path=self.voz, **ESTILO)
        return w.squeeze(0).cpu().numpy()


class Piper:
    nombre = 'Piper es_MX-claude-high (voz MIT, motor GPL-3.0)'

    def __init__(self):
        import descargar
        from piper import PiperVoice
        dest = DATOS / 'piper'
        modelo = dest / PIPER_VOZ[2][0]
        if not modelo.exists():
            print('Bajando la voz de Piper (~60 MB) …', flush=True)
            for a in PIPER_VOZ[2]:
                descargar.archivo(f'{descargar.HF}/{PIPER_VOZ[0]}/resolve/main/{PIPER_VOZ[1]}{a}', dest / a)
        self.voz = PiperVoice.load(str(modelo))
        self.sr = self.voz.config.sample_rate

    def decir(self, texto, intento, semilla):
        import io, numpy as np
        from piper import SynthesisConfig
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            self.voz.synthesize_wav(texto, w, syn_config=SynthesisConfig(**PIPER_VARIANTES[(intento - 1) % 3]))
        buf.seek(0)
        with wave.open(buf, 'rb') as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return x


# ---------- narrar ----------
def pausa(f, sig):
    if f['texto'].rstrip().endswith(('?', '!', '…')) or (sig.get('bloque') and sig.get('bloque') != f.get('bloque')):
        return PAUSA_LARGA
    return PAUSA_CORTA if len(f['texto'].split()) <= 3 else PAUSA_NORMAL


def narrar(o):
    import numpy as np, soundfile as sf
    from oido import errores, norm, tiempos, transcribir
    t0 = time.time()
    frases = frases_de(o.guion)
    out = Path(o.salida); (out / 'frases').mkdir(parents=True, exist_ok=True)
    voz = None
    if o.motor == 'chatterbox':
        if not o.voz:
            print('Falta --voz voces/mi_voz.json (primero: ia.py voz revisar-muestra --muestra mi_voz.wav --es-mi-voz).'); return 2
        voz = leer_json(o.voz)
        if not voz.get('declaracion'):
            print('ALTO: esa muestra no tiene la confirmación de que es tu voz. Regístrala con revisar-muestra --es-mi-voz.'); return 2
    clave = o.motor + (hashlib.sha1(voz['audio'].encode()).hexdigest()[:6] if voz else '')
    rehacer = {i.strip() for i in (o.rehacer or '').split(',') if i.strip()}
    motor = None
    calidad = []
    for f in frases:
        base = out / 'frases' / f"{f['id']}_{clave}_{hashlib.sha1(f['texto'].encode()).hexdigest()[:8]}"
        if base.with_suffix('.wav').exists() and base.with_suffix('.json').exists() and f['id'] not in rehacer:
            calidad.append(leer_json(base.with_suffix('.json'))); continue
        if motor is None:
            motor = Chatterbox(voz, o.cpu) if o.motor == 'chatterbox' else Piper()
        ref = norm(f['texto'])
        maximo = max(4.0, len(ref) * 0.9)  # una frase que sale mucho más larga se desbocó: cuenta como intento fallido
        mejor = None
        for intento in range(1, o.intentos + 1):
            t = time.time()
            x = recorte(motor.decir(f['texto'], intento, 1000 * len(calidad) + intento), motor.sr)
            dur = len(x) / motor.sr
            tmp = base.with_name(base.name + f'_i{intento}.wav'); sf.write(str(tmp), x, motor.sr)
            if dur > maximo:
                oido, palabras, err = '(se desbocó: audio demasiado largo)', [], len(ref)
            else:
                segs, _ = transcribir(str(tmp), o.whisper)
                palabras = [p for s in segs for p in s['palabras']]
                oido = ' '.join(p['w'] for p in palabras)
                err = errores(ref, norm(oido))
            print(f"  {f['id']} intento {intento}: {err} error(es) · {dur:.1f} s en {time.time() - t:.0f} s · «{oido}»", flush=True)
            if mejor is None or err < mejor['errores']:
                if mejor:
                    Path(mejor['tmp']).unlink(missing_ok=True)
                mejor = dict(tmp=str(tmp), oido=oido, palabras=palabras, errores=err, intento=intento, dur=round(dur, 2))
            else:
                tmp.unlink(missing_ok=True)
            if err == 0:
                break
        Path(mejor['tmp']).replace(base.with_suffix('.wav'))
        c = {'id': f['id'], 'texto': f['texto'], 'oido': mejor['oido'], 'palabras_guion': len(ref), 'errores': mejor['errores'],
             'intentos': intento, 'elegido': mejor['intento'], 'dur': mejor['dur'], 'marcas': mejor['palabras'], 'wav': base.with_suffix('.wav').name}
        escribir_json(base.with_suffix('.json'), c)
        calidad.append(c)
    del motor
    # unir con pausas y sacar los tiempos de cada palabra
    sr = None; trozos = []; T = []; t = 0.0
    for i, (f, c) in enumerate(zip(frases, calidad)):
        x, s = sf.read(str(out / 'frases' / c['wav']), dtype='float32')
        sr = sr or s
        if s != sr:
            x = np.interp(np.linspace(0, len(x), int(len(x) * sr / s), endpoint=False), np.arange(len(x)), x).astype(np.float32)
        pal = tiempos(f['texto'], c['marcas'], t)
        T.append({'id': f['id'], 'texto': f['texto'], 'ini': pal[0]['s'], 'fin': pal[-1]['e'], 'palabras': pal, 'oido': c['oido']})
        trozos.append(x); t += len(x) / sr
        if i < len(frases) - 1:
            p = pausa(f, frases[i + 1]); c['pausa_despues'] = p
            trozos.append(np.zeros(int((p - ORILLAS) * sr), np.float32)); t += p - ORILLAS
    trozos.append(np.zeros(int(0.4 * sr), np.float32))
    total = np.concatenate(trozos)
    sf.write(str(out / 'narracion.wav'), total, sr)
    dur = round(len(total) / sr, 2)
    escribir_json(out / 'tiempos.json', {'dur': dur, 'frases': T})
    n_ref = sum(c['palabras_guion'] for c in calidad); n_err = sum(c['errores'] for c in calidad)
    wer = round(100 * n_err / max(1, n_ref), 2)
    escribir_json(out / 'calidad.json', {'motor': (Chatterbox if o.motor == 'chatterbox' else Piper).nombre, 'duracion_s': dur,
                                         'palabras_guion': n_ref, 'errores_por_palabra': n_err, 'error_pct': wer,
                                         'frases_sin_error': sum(c['errores'] == 0 for c in calidad), 'frases': len(calidad),
                                         'minutos': round((time.time() - t0) / 60, 2),
                                         'detalle': [{k: v for k, v in c.items() if k != 'marcas'} for c in calidad]})
    print(f'\nnarracion.wav: {dur:.1f} s · {len(calidad)} frases · error por palabra {wer} % ({n_err} de {n_ref}) · {time.time() - t0:.0f} s')
    malas = [c for c in calidad if c['errores']]
    if malas:
        print('REVISA (después de 3 intentos todavía no se oyen igual al guion; escúchalas):')
        for c in malas:
            print(f"  {c['id']}: guion «{c['texto']}» · se oyó «{c['oido']}»")
    print('NARRACION_OK')
    return 0


def main(_cmd, resto):
    a = argparse.ArgumentParser(prog='ia.py voz')
    s = a.add_subparsers(dest='accion', required=True)
    m = s.add_parser('revisar-muestra'); m.add_argument('--muestra', required=True); m.add_argument('--salida', default='voces/mi_voz')
    m.add_argument('--es-mi-voz', action='store_true'); m.add_argument('--tengo-permiso')
    n = s.add_parser('narrar'); n.add_argument('--guion', required=True); n.add_argument('--salida', default='voz')
    n.add_argument('--motor', choices=['chatterbox', 'piper'], required=True); n.add_argument('--voz', help='voces/mi_voz.json (solo chatterbox)')
    n.add_argument('--intentos', type=int, default=3); n.add_argument('--rehacer', help='ids separados por coma: p03,p05')
    n.add_argument('--cpu', action='store_true', help='Chatterbox sin tarjeta (muy lento)'); n.add_argument('--whisper', default='large-v3-turbo')
    o = a.parse_args(resto)
    return {'revisar-muestra': revisar_muestra, 'narrar': narrar}[o.accion](o)
