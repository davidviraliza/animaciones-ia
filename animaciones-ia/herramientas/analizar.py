"""Analiza un video de referencia: cortes de escena, cuadros del gancho y de cada toma, hojas de contacto y transcripción.
Si le das un ENLACE, lo baja con yt-dlp SOLO para estudiarlo (nunca para resubirlo ni usar su material).
Claude no ve el video en movimiento: ve los cuadros fijos que salen de aquí y lee la transcripción con tiempos."""
import argparse, json, re, shutil, subprocess, sys, time
from pathlib import Path
from comun import correr, duracion, escribir_json


def cortes(video, umbral):
    r = correr(['ffmpeg', '-hide_banner', '-i', str(video), '-filter:v', f"select='gt(scene,{umbral})',showinfo", '-an', '-f', 'null', '-'])
    return [round(float(m), 2) for m in re.findall(r'pts_time:([0-9.]+)', r.stderr)]


def cuadro(video, t, dest, ancho=360):
    correr(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', str(video), '-frames:v', '1', '-vf', f'scale={ancho}:-2', '-q:v', '3', str(dest)])


def bajar(url, carpeta):
    """yt-dlp con progreso visible y reintentos. Devuelve (ruta del mp4, ficha)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    print('Bajando la referencia SOLO para estudiarla (no se publica ni se reutiliza su material) …', flush=True)
    for intento in range(1, 4):
        r = subprocess.run([sys.executable, '-m', 'yt_dlp', '--newline', '--no-playlist', '--retries', '10', '--socket-timeout', '30',
                            '-f', 'bv*[height<=1080]+ba/b[height<=1080]/b', '--merge-output-format', 'mp4', '--write-info-json',
                            '-o', str(carpeta / 'referencia.%(ext)s'), url])
        mp4 = carpeta / 'referencia.mp4'
        if r.returncode == 0 and mp4.exists() and mp4.stat().st_size > 0:
            break
        print(f'La descarga falló (intento {intento} de 3). Reintento en 5 s …', flush=True); time.sleep(5)
    else:
        raise SystemExit('No pude bajar el enlace. Si es privado o pide sesión, bájalo tú desde el teléfono y pásame el archivo.')
    ficha = {}
    info = carpeta / 'referencia.info.json'
    if info.exists():
        d = json.loads(info.read_text(encoding='utf-8'))
        ficha = {k: d.get(k) for k in ('title', 'uploader', 'channel', 'duration', 'view_count', 'like_count', 'comment_count', 'upload_date', 'width', 'height', 'webpage_url')}
        (carpeta / 'ficha.json').write_text(json.dumps(ficha, ensure_ascii=False, indent=1), encoding='utf-8')
        info.unlink()
    return mp4, ficha


def main(_cmd, resto):
    a = argparse.ArgumentParser(prog='ia.py analizar')
    a.add_argument('video'); a.add_argument('carpeta')
    a.add_argument('--umbral', type=float, default=0.3, help='sensibilidad de corte (0.2 = más cortes)')
    a.add_argument('--modelo', default='large-v3-turbo', help='whisper: large-v3-turbo (mejor) o small (más rápido)')
    a.add_argument('--sin-voz', action='store_true', help='no transcribir')
    o = a.parse_args(resto)
    t0 = time.time()
    out = Path(o.carpeta).resolve(); ficha = {}
    if re.match(r'https?://', o.video):
        v, ficha = bajar(o.video, out.parent)
    else:
        v = Path(o.video).resolve()
    if not v.exists():
        print(f'No encuentro {v}'); return 2
    for d in ('cuadros', 'gancho', 'hojas'):
        shutil.rmtree(out / d, ignore_errors=True); (out / d).mkdir(parents=True)
    dur = duracion(v)
    cs = cortes(v, o.umbral)
    tomas = list(zip([0.0] + cs, cs + [dur]))
    print(f'{dur:.1f} s, {len(cs)} cortes, {len(tomas)} tomas', flush=True)
    # gancho: cada medio segundo de 0 a 3 s, más grande
    for k in range(7):
        cuadro(v, min(k * 0.5, max(0, dur - 0.05)), out / 'gancho' / f'g{k:02d}_{k * 0.5:.1f}s.jpg', 540)
    # una imagen a la mitad de cada toma (máx. 48), numeradas en orden para las hojas de contacto
    paso = max(1, len(tomas) // 48 + (len(tomas) % 48 > 0))
    elegidas = tomas[::paso]
    for i, (s, e) in enumerate(elegidas):
        cuadro(v, (s + e) / 2, out / 'cuadros' / f'c_{i + 1:03d}.jpg')
    correr(['ffmpeg', '-v', 'error', '-y', '-i', str(out / 'cuadros' / 'c_%03d.jpg'), '-vf', 'scale=270:-2,tile=4x3:padding=6:color=white', str(out / 'hojas' / 'hoja_%02d.jpg')])
    seg, idioma = [], None
    if not o.sin_voz:
        wav = out / 'audio16k.wav'
        correr(['ffmpeg', '-v', 'error', '-y', '-i', str(v), '-ac', '1', '-ar', '16000', str(wav)])
        from oido import transcribir
        seg, idioma = transcribir(wav, o.modelo, idioma=None)
        wav.unlink(missing_ok=True)
    palabras = [p for s in seg for p in s['palabras']]
    gancho_txt = ' '.join(p['w'] for p in palabras if p['s'] < 3.0)
    habla = sum(p['e'] - p['s'] for p in palabras)
    escribir_json(out / 'analisis.json', {'video': v.name, 'dur': dur, 'cortes': cs, 'tomas': [{'n': i + 1, 'ini': s, 'fin': e} for i, (s, e) in enumerate(tomas)],
                                         'idioma': idioma, 'segmentos': seg})
    L = [f'# Análisis base de {v.name}', '', '> Claude no ve el video en movimiento: ve estos cuadros fijos y lee la transcripción con tiempos. El ritmo y los cortes salen de medir, no de «ver».', '',
         *([f"- Ficha (de la página): {ficha.get('title') or '—'} · cuenta {ficha.get('uploader') or ficha.get('channel') or '—'} · "
             f"vistas {ficha.get('view_count') or '—'} · likes {ficha.get('like_count') or '—'} · comentarios {ficha.get('comment_count') or '—'} · "
             f"publicado {ficha.get('upload_date') or '—'}"] if ficha else []),
         f'- Duración: {dur:.1f} s · cortes detectados: {len(cs)} · toma promedio: {dur / max(1, len(tomas)):.2f} s · cortes por minuto: {len(cs) / max(dur, 1) * 60:.0f}',
         f'- Idioma: {idioma or "—"} · palabras: {len(palabras)} · palabras por segundo de video: {len(palabras) / max(dur, 1):.2f} · tiempo hablando: {habla / max(dur, 1) * 100:.0f} %',
         f'- Primeros 3 s (gancho), dice: «{gancho_txt}»', f'- Primera palabra en: {palabras[0]["s"]:.2f} s' if palabras else '- Sin voz detectada', '',
         '## Cuadros', '- `gancho/`: 0, 0.5, 1 … 3 s (540 px de ancho)', f'- `hojas/hoja_NN.jpg`: 12 tomas por hoja, en orden (una imagen a la mitad de cada toma{", cada " + str(paso) + " tomas" if paso > 1 else ""})', '',
         '## Tomas', '| # | ini | fin | dura | imagen |', '|---|---|---|---|---|']
    for i, (s, e) in enumerate(tomas):
        img = f'c_{i // paso + 1:03d}' if i % paso == 0 else ''
        L.append(f'| {i + 1} | {s:.2f} | {e:.2f} | {e - s:.2f} | {img} |')
    L += ['', '## Transcripción con tiempos', ''] + [f'- [{s["ini"]:.1f}–{s["fin"]:.1f}] {s["texto"]}' for s in seg]
    (out / 'ANALISIS_BASE.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'Listo en {time.time() - t0:.0f} s → {out / "ANALISIS_BASE.md"}')
    return 0
