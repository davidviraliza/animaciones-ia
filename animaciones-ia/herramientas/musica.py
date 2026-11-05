"""Música original para tu video (compositor.py, síntesis con numpy, sin samples ni canciones de nadie).
Secciones que siguen el guion: entrada, desarrollo, tensión antes del giro y cierre. Efectos de golpe en las palabras que digas."""
import argparse, random, time
from pathlib import Path
import numpy as np
from compositor import NOTAS, SR, Cancion, golpe, guardar
from comun import duracion, escribir_json, leer_json, norm


def buscar(tiempos, ref):
    """'p04' → inicio de esa frase; 'p04:corteza' → inicio de la palabra que empieza con «corteza» en p04; '12.5' → 12.5 s."""
    try:
        return float(ref)
    except ValueError:
        pass
    fid, _, pal = ref.partition(':')
    f = next((x for x in tiempos['frases'] if x['id'] == fid), None)
    if f is None:
        raise SystemExit(f'No encuentro la frase {fid} en tiempos.json')
    if not pal:
        return f['ini']
    for p in f['palabras']:
        if norm(p['w']).startswith(norm(pal)):
            return p['s']
    raise SystemExit(f'No encuentro «{pal}» en {fid}: «{f["texto"]}»')


def main(_cmd, resto):
    a = argparse.ArgumentParser(prog='ia.py musica')
    a.add_argument('--salida', required=True)
    a.add_argument('--dur', type=float, help='segundos; si no la das, usa la de --voz')
    a.add_argument('--voz', help='narracion.wav: la música dura lo mismo')
    a.add_argument('--tiempos', help='voz/tiempos.json, para --giro y --golpes por frase y palabra')
    a.add_argument('--giro', help='dónde está el giro del guion: p05, p05:pero o segundos. Antes del giro, la música sube la tensión')
    a.add_argument('--golpes', help='efectos de golpe separados por coma: p02:indico,p04,13.2 → sale efectos.wav junto a la música')
    a.add_argument('--semilla', type=int, help='otra semilla = otra canción; si no la das, se elige una al azar')
    a.add_argument('--bpm', type=float, default=140)
    a.add_argument('--tono', choices=list(NOTAS), help='tonalidad; al azar si no la das')
    o = a.parse_args(resto)
    dur = o.dur or (duracion(o.voz) if o.voz else None)
    if not dur:
        print('Dame --dur o --voz'); return 2
    tiempos = leer_json(o.tiempos) if o.tiempos else None
    if (o.giro or o.golpes) and not tiempos and not all(x.replace('.', '').isdigit() for x in f'{o.giro or ""},{o.golpes or ""}'.split(',') if x):
        print('Para --giro o --golpes con frases o palabras, pasa también --tiempos voz/tiempos.json'); return 2
    rnd = random.SystemRandom()
    semilla = o.semilla if o.semilla is not None else rnd.randrange(1, 10**6)
    tono = o.tono or rnd.choice(['C', 'D', 'E', 'F', 'G', 'A'])
    t = time.time()
    c = Cancion(semilla, o.bpm, tono, dur)
    compas = 4 * c.beat
    entrada = min(2 * compas, dur * 0.2)
    cierre = max(entrada, dur - min(4.0, dur * 0.15))
    giro = buscar(tiempos, o.giro) if o.giro else None
    secciones = []
    if giro and entrada + compas < giro < cierre:
        tension = max(entrada, giro - 2 * compas)
        secciones = [(0, entrada, 'intro'), (entrada, tension, 'drop'), (tension, giro, 'tension'), (giro, cierre, 'drop'), (cierre, dur, 'final')]
    else:
        secciones = [(0, entrada, 'intro'), (entrada, cierre, 'drop'), (cierre, dur, 'final')]
    for s in secciones:
        if s[1] - s[0] > 0.05:
            c.seccion(*s)
    Path(o.salida).parent.mkdir(parents=True, exist_ok=True)
    guardar(c.render(), o.salida)
    golpes = [round(buscar(tiempos, g.strip()), 3) for g in o.golpes.split(',') if g.strip()] if o.golpes else []
    efectos = None
    if golpes:
        x = np.zeros((int((dur + 1) * SR), 2), np.float32)
        for k, g0 in enumerate(golpes):
            gl = golpe(semilla + k); i = int(g0 * SR); m = min(len(gl), len(x) - i)
            if m > 0:
                x[i:i + m] += gl[:m]
        efectos = str(Path(o.salida).with_name('efectos.wav'))
        guardar((x[:int(dur * SR)] / max(1e-6, np.abs(x).max()) * 0.89).astype(np.float32), efectos)
    escribir_json(Path(o.salida).with_suffix('.json'), {'semilla': semilla, 'bpm': o.bpm, 'tono': tono, 'dur': dur,
                                                       'secciones': [[round(a, 2), round(b, 2), s] for a, b, s in secciones],
                                                       'golpes': golpes, 'efectos': efectos,
                                                       'nota': 'Música original sintetizada por compositor.py; la misma semilla reproduce el mismo audio.'})
    print(f'Música original: {dur:.1f} s, semilla {semilla}, tono {tono} menor, {o.bpm:g} bpm, secciones '
          + ' → '.join(f'{s} {a:.1f}–{b:.1f}' for a, b, s in secciones)
          + (f', {len(golpes)} golpes en efectos.wav' if golpes else '') + f', en {time.time() - t:.0f} s → {o.salida}')
    return 0
