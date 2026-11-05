"""Hoja de contacto para el revisor: un cuadro por frase, a tamaño completo, más el cuadro 0 y el último.
    --video entrega/final.mp4   saca los cuadros del video ya renderizado
    --remotion video            antes del render: pide los cuadros fijos a Remotion (un solo empaquetado, rápido)
Además marca lo que hay que mirar con lupa (no aprueba nada: eso lo decides mirando):
    PLANO      el cuadro casi no tiene detalle (fondo liso, poca textura)
    VACÍO      más de la mitad del cuadro es una sola superficie lisa
    REPETIDO   se parece casi igual a otro cuadro de otra frase (posible toma repetida)
Sale: <salida>/cuadros/NN_<id>.png, <salida>/hoja.jpg y <salida>/HOJA.md"""
import argparse, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from comun import correr, escribir_json, leer_json

W, H, FPS = 1080, 1920, 30


def momentos(tiempos):
    """Cuadro 0, el centro de cada frase y el último."""
    m = [('inicio', 0.0, '(cuadro 0)')]
    for f in tiempos['frases']:
        m.append((f['id'], round((f['ini'] + f['fin']) / 2, 2), f['texto']))
    m.append(('final', max(0.0, tiempos['dur'] - 0.2), '(último cuadro)'))
    return m


def gris(png):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(png), '-vf', 'scale=108:192,format=gray', '-f', 'rawvideo', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(192, 108).astype(np.float32)


def main(_cmd, resto):
    a = argparse.ArgumentParser(prog='ia.py hoja')
    a.add_argument('--tiempos', required=True, help='voz/tiempos.json')
    a.add_argument('--video', help='mp4 ya renderizado')
    a.add_argument('--remotion', help='carpeta del proyecto de Remotion (video/), para cuadros antes del render')
    a.add_argument('--salida', required=True)
    o = a.parse_args(resto)
    if not (o.video or o.remotion):
        print('Dame --video o --remotion'); return 2
    t = leer_json(o.tiempos)
    out = Path(o.salida); cdir = out / 'cuadros'
    shutil.rmtree(cdir, ignore_errors=True); cdir.mkdir(parents=True)
    ms = momentos(t)
    nombres = [cdir / f'{k:02d}_{mid}.png' for k, (mid, _, _) in enumerate(ms)]
    if o.video:
        for (mid, s, _), n in zip(ms, nombres):
            correr(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s:.3f}', '-i', o.video, '-frames:v', '1', str(n)])
    else:
        cuadros = ','.join(f'{int(round(s * FPS))}:{n.resolve()}' for (_, s, _), n in zip(ms, nombres))
        npx = 'npx.cmd' if sys.platform == 'win32' else 'npx'
        r = subprocess.run(['node', 'cuadros.mjs', cuadros], cwd=o.remotion)
        if r.returncode != 0:
            print(f'Remotion no pudo sacar los cuadros (código {r.returncode}). Prueba uno a mano: {npx} remotion still src/index.ts Video salida/x.png --frame=0'); return 1
    faltan = [n.name for n in nombres if not n.exists()]
    if faltan:
        print('No salieron: ' + ', '.join(faltan)); return 1
    # medidas para mirar con lupa
    g = [gris(n) for n in nombres]
    filas = []
    for k, ((mid, s, txt), n, x) in enumerate(zip(ms, nombres, g)):
        detalle = float(np.mean(np.abs(np.diff(x, axis=0))) + np.mean(np.abs(np.diff(x, axis=1))))
        bloques = x.reshape(24, 8, 12, 9).std(axis=(1, 3))  # 24×12 bloques de 8×9 px
        liso = float(np.mean(bloques < 2.0))
        parecidos = [ms[j][0] for j in range(len(g)) if j != k and ms[j][0] not in ('inicio', 'final') and mid not in ('inicio', 'final')
                     and float(np.mean(np.abs(g[j] - x))) < 4.0]
        marcas = (['PLANO'] if detalle < 4.0 else []) + (['VACÍO'] if liso > 0.5 else []) + (['REPETIDO con ' + ', '.join(parecidos)] if parecidos else [])
        filas.append({'n': k, 'id': mid, 't': s, 'texto': txt, 'archivo': f'cuadros/{n.name}', 'detalle': round(detalle, 1),
                      'liso_pct': round(100 * liso), 'marcas': marcas})
    # hoja: 5 columnas, en orden
    tmp = out / '_hoja'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    for k, n in enumerate(nombres):
        shutil.copy(n, tmp / f'h_{k:03d}.png')
    filas_hoja = (len(nombres) + 4) // 5
    correr(['ffmpeg', '-v', 'error', '-y', '-i', str(tmp / 'h_%03d.png'), '-vf', f'scale=270:480,tile=5x{filas_hoja}:padding=8:color=white',
            '-frames:v', '1', '-q:v', '3', str(out / 'hoja.jpg')])
    shutil.rmtree(tmp, ignore_errors=True)
    L = ['# Hoja de contacto', '', f'`hoja.jpg`: {len(nombres)} cuadros en orden (5 por fila): cuadro 0, una por frase (a la mitad), último.',
         'Las marcas solo dicen qué mirar con lupa; abre a tamaño completo los marcados y los dudosos.', '',
         '| # | frase | s | texto | detalle | liso % | marcas |', '|---|---|---|---|---|---|---|']
    L += [f"| {f['n']} | {f['id']} | {f['t']:.2f} | {f['texto'][:60]} | {f['detalle']} | {f['liso_pct']} | {' · '.join(f['marcas']) or '—'} |" for f in filas]
    (out / 'HOJA.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    escribir_json(out / 'hoja.json', filas)
    marcados = [f for f in filas if f['marcas']]
    print(f"Hoja: {out / 'hoja.jpg'} · {len(nombres)} cuadros en {cdir} · marcados para mirar: "
          + (', '.join(f"{f['id']} ({' · '.join(f['marcas'])})" for f in marcados) if marcados else 'ninguno'))
    return 0
