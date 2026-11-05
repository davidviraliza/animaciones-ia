"""Acabado: voz + música (unos 18 dB debajo de la voz) + efectos de golpe, volumen final a -14 LUFS con picos bajo -1 dBTP
(lo que usan TikTok, Reels y YouTube), y pega el audio al video de Remotion. Mide el resultado y lo dice."""
import argparse, json, re, time
from pathlib import Path
from comun import correr, duracion, escribir_json

LUFS, PICO = -14.0, -1.5


def medir(archivo):
    """(LUFS integrado, pico real en dBTP)."""
    r = correr(['ffmpeg', '-hide_banner', '-nostats', '-i', str(archivo), '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    i = re.findall(r'I:\s+(-?[0-9.]+) LUFS', r.stderr); p = re.findall(r'Peak:\s+(-?[0-9.]+) dBFS', r.stderr)
    return (float(i[-1]) if i else None), (float(p[-1]) if p else None)


def main(_cmd, resto):
    a = argparse.ArgumentParser(prog='ia.py acabado')
    a.add_argument('--video', required=True, help='render.mp4 de Remotion (sin audio)')
    a.add_argument('--voz', required=True, help='narracion.wav')
    a.add_argument('--musica', help='musica.wav (opcional)')
    a.add_argument('--efectos', help='efectos.wav de ia.py musica --golpes (opcional)')
    a.add_argument('--salida', required=True, help='final.mp4')
    a.add_argument('--bajo-voz', type=float, default=18, help='cuántos dB debajo de la voz va la música (18 = como en el tutorial)')
    o = a.parse_args(resto)
    t0 = time.time()
    out = Path(o.salida); out.parent.mkdir(parents=True, exist_ok=True)
    mezcla = out.with_name(out.stem + '_mezcla.wav'); final_wav = out.with_name(out.stem + '_audio.wav')
    dv = duracion(o.video)
    lv, pv = medir(o.voz)
    entradas = ['-i', o.voz]; f = ['[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0[v]']; mix = ['[v]']
    info = {'voz_lufs': lv}
    if o.musica:
        lm, _ = medir(o.musica)
        g = (lv - o.bajo_voz) - lm
        entradas += ['-i', o.musica]; f.append(f'[1:a]aresample=48000,volume={g:.2f}dB[m]'); mix.append('[m]')
        info.update(musica_lufs_original=lm, musica_ganancia_db=round(g, 2), musica_bajo_voz_db=o.bajo_voz)
    if o.efectos:
        _, pe = medir(o.efectos)
        g = (pv - 4) - pe  # el golpe se oye, pero su pico queda 4 dB abajo del pico de la voz
        k = len(entradas) // 2
        entradas += ['-i', o.efectos]; f.append(f'[{k}:a]aresample=48000,volume={g:.2f}dB[e]'); mix.append('[e]')
        info.update(efectos_ganancia_db=round(g, 2))
    f.append(''.join(mix) + f'amix=inputs={len(mix)}:normalize=0:duration=first,apad,atrim=0:{dv:.3f}[s]')
    r = correr(['ffmpeg', '-v', 'error', '-y', *entradas, '-filter_complex', ';'.join(f), '-map', '[s]', '-c:a', 'pcm_s24le', str(mezcla)])
    if r.returncode != 0:
        print(r.stderr[-1500:]); return 1
    # loudnorm en dos pasadas: primero mide, luego corrige de forma lineal
    r = correr(['ffmpeg', '-hide_banner', '-nostats', '-i', str(mezcla), '-af', f'loudnorm=I={LUFS}:TP={PICO}:LRA=11:print_format=json', '-f', 'null', '-'])
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    filtro = (f"loudnorm=I={LUFS}:TP={PICO}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    r = correr(['ffmpeg', '-v', 'error', '-y', '-i', str(mezcla), '-af', filtro, '-c:a', 'pcm_s24le', str(final_wav)])
    if r.returncode != 0:
        print(r.stderr[-1500:]); return 1
    r = correr(['ffmpeg', '-v', 'error', '-y', '-i', o.video, '-i', str(final_wav), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{dv:.3f}', str(out)])
    if r.returncode != 0:
        print(r.stderr[-1500:]); return 1
    lufs, pico = medir(out)
    ok = lufs is not None and abs(lufs - LUFS) <= 0.5 and pico is not None and pico <= -1.0
    escribir_json(out.with_suffix('.json'), {'lufs': lufs, 'pico_dbtp': pico, 'dur_video': dv, 'dur_final': duracion(out), **info,
                                             'segundos': round(time.time() - t0, 1)})
    print(f"{out}: {duracion(out):.2f} s · {lufs} LUFS (meta {LUFS:g}) · pico {pico} dBTP (meta bajo -1) · "
          f"música {o.bajo_voz:g} dB bajo la voz · {'OK' if ok else 'REVISAR'} · {time.time() - t0:.0f} s")
    return 0 if ok else 1
