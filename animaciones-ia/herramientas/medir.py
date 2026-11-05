"""Medición del video terminado (la usa el revisor antes de dártelo):
formato, duración, volumen (-14 LUFS), picos (bajo -1 dBTP), cuadro 0 con algo que ver,
y la transcripción del video contra el guion (palabras cambiadas, sobrantes y faltantes).
Sale: <salida>/MEDICION.md y medicion.json"""
import argparse, json, subprocess
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np
from acabado import medir as loudness
from comun import correr, escribir_json, frases_de


def main(_cmd, resto):
    from oido import errores, norm, transcribir
    a = argparse.ArgumentParser(prog='ia.py medir')
    a.add_argument('--video', required=True); a.add_argument('--guion', required=True); a.add_argument('--salida', required=True)
    a.add_argument('--whisper', default='large-v3-turbo')
    o = a.parse_args(resto)
    out = Path(o.salida); out.mkdir(parents=True, exist_ok=True)
    r = correr(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate:format=duration', '-of', 'json', o.video])
    pr = json.loads(r.stdout)
    v = next(s for s in pr['streams'] if s['codec_type'] == 'video'); au = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    dur = float(pr['format']['duration'])
    lufs, pico = loudness(o.video)
    x = subprocess.run(['ffmpeg', '-v', 'error', '-i', o.video, '-frames:v', '1', '-vf', 'scale=108:192,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    c0 = float(np.frombuffer(x, np.uint8).astype(np.float32).std()) if x else 0.0
    wav = out / '_audio16k.wav'
    correr(['ffmpeg', '-v', 'error', '-y', '-i', o.video, '-ac', '1', '-ar', '16000', str(wav)])
    segs, _ = transcribir(str(wav), o.whisper)
    wav.unlink(missing_ok=True)
    oido = ' '.join(s['texto'] for s in segs)
    guion = ' '.join(f['texto'] for f in frases_de(o.guion))
    ref, hip = norm(guion), norm(oido)
    err = errores(ref, hip); wer = round(100 * err / max(1, len(ref)), 2)
    difs = [f"{tag}: «{' '.join(ref[i1:i2])}» → «{' '.join(hip[j1:j2])}»" for tag, i1, i2, j1, j2 in SequenceMatcher(None, ref, hip, autojunk=False).get_opcodes() if tag != 'equal']
    pruebas = [
        ('Formato', f"{v['codec_name']} {v['width']}×{v['height']} a {v['r_frame_rate']} fps · audio {au[0]['codec_name'] if au else 'NO HAY'}",
         v['width'] == 1080 and v['height'] == 1920 and bool(au)),
        ('Duración', f'{dur:.2f} s', dur > 0),
        ('Volumen', f'{lufs} LUFS (meta −14 ± 0.5)', lufs is not None and abs(lufs + 14) <= 0.5),
        ('Picos', f'{pico} dBTP (meta bajo −1)', pico is not None and pico <= -1.0),
        ('Cuadro 0', f'variación {c0:.1f} (bajo 8 = casi liso o negro)', c0 >= 8),
        ('Transcripción contra guion', f'{err} de {len(ref)} palabras distintas = {wer} % (0 es lo ideal; más de 2 % se revisa)', wer <= 2.0),
    ]
    L = ['# Medición del video', '', f'`{o.video}`', '', '| Prueba | Resultado | ¿Pasa? |', '|---|---|---|']
    L += [f"| {n} | {res} | {'sí' if ok else 'NO'} |" for n, res, ok in pruebas]
    L += ['', '## Diferencias contra el guion (whisper puede oír mal nombres propios: escúchalas antes de rehacer)', '']
    L += [f'- {d}' for d in difs] or ['- ninguna']
    L += ['', '## Lo que no mide esta herramienta', '- Cómo suena: hay que oírlo con audífonos y en la bocina del celular.',
          '- Cómo se siente el movimiento: hay que ver el video corriendo.']
    (out / 'MEDICION.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    escribir_json(out / 'medicion.json', {'pruebas': [{'prueba': n, 'resultado': res, 'pasa': ok} for n, res, ok in pruebas],
                                          'oido': oido, 'diferencias': difs, 'wer_pct': wer, 'lufs': lufs, 'pico_dbtp': pico, 'dur': dur})
    for n, res, ok in pruebas:
        print(f"  {'OK ' if ok else 'NO '} {n}: {res}")
    print(f"MEDICION_{'OK' if all(ok for _, _, ok in pruebas) else 'REVISAR'} → {out / 'MEDICION.md'}")
    return 0
