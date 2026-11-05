"""Descargas largas que no se atoran: HTTP directo, progreso visible y reintento.

- Muestra MB bajados y velocidad cada ~10 s (para que se vea que avanza).
- Si en 60 s no llega ni un byte (o el archivo se queda en 0 bytes), corta y reintenta, reanudando donde se quedó.
- Hasta 5 intentos por archivo. Así evitamos lo que pasa con algunas descargas de modelos que se quedan quietas sin avisar.
Solo biblioteca estándar.
"""
import fnmatch, json, os, socket, time, urllib.request
from pathlib import Path

HF = 'https://huggingface.co'
SIN_AVANCE_S = 60
INTENTOS = 5
PEDAZO = 48 * 2**20  # cada pedazo con conexión nueva: una sola conexión larga se va frenando


def _abrir(url, desde=0, hasta=None):
    rango = {'Range': f'bytes={desde}-{"" if hasta is None else hasta}'} if (desde or hasta is not None) else {}
    req = urllib.request.Request(url, headers={'User-Agent': 'animaciones-ia/0.2', **rango})
    return urllib.request.urlopen(req, timeout=SIN_AVANCE_S)


def _tamano(url):
    """Tamaño total si el servidor deja pedir pedazos; None si no."""
    try:
        with _abrir(url, 0, 0) as r:
            cr = r.headers.get('Content-Range') or ''
            return int(cr.rsplit('/', 1)[1]) if r.status == 206 and '/' in cr and cr.rsplit('/', 1)[1].isdigit() else None
    except (OSError, ValueError):
        return None


def archivo(url, dest, nombre=None):
    """Baja url a dest por pedazos (reanuda si ya hay uno). Devuelve la ruta. Lanza SystemExit si falla 5 veces seguidas."""
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    nombre = nombre or dest.name
    parcial = dest.with_name(dest.name + '.parcial')
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    total = _tamano(url)
    ya = parcial.stat().st_size if parcial.exists() else 0
    if not total:
        ya = 0; parcial.unlink(missing_ok=True)  # sin pedazos: de un jalón
    print(f'  bajando {nombre} ({(total or 0) / 2**20:.0f} MB){" · reanudo en " + str(ya // 2**20) + " MB" if ya else ""}', flush=True)
    t0 = t_aviso = time.time(); inicio = ya; fallas = 0
    while True:
        try:
            with _abrir(url, ya, min(ya + PEDAZO, total) - 1 if total else None) as r, open(parcial, 'ab') as f:
                while True:
                    bloque = r.read(1 << 20)  # si en 60 s no llega nada, se corta y se reintenta
                    if not bloque:
                        break
                    f.write(bloque); ya += len(bloque); fallas = 0
                    if time.time() - t_aviso >= 10:
                        vel = (ya - inicio) / max(0.1, time.time() - t0) / 2**20
                        pct = f'{ya / total * 100:.0f} %' if total else ''
                        print(f'    {nombre}: {ya / 2**20:.0f} de {(total or 0) / 2**20:.0f} MB {pct} · {vel:.1f} MB/s', flush=True)
                        t_aviso = time.time()
            if not total or ya >= total:
                if ya == 0:
                    raise OSError('llegaron 0 bytes')
                break
        except (OSError, socket.timeout) as e:
            fallas += 1
            if fallas > INTENTOS:
                raise SystemExit(f'No pude bajar {nombre} tras {INTENTOS} intentos. Revisa tu internet y vuelve a correr el mismo comando: reanuda donde se quedó.')
            print(f'    {nombre}: se detuvo ({e}). Reintento {fallas} de {INTENTOS} en 5 s, reanudando en {ya // 2**20} MB…', flush=True)
            time.sleep(5)
            if not total:
                ya = 0; parcial.unlink(missing_ok=True)
    parcial.replace(dest)
    print(f'    {nombre}: listo ({dest.stat().st_size / 2**20:.0f} MB en {time.time() - t0:.0f} s)', flush=True)
    return dest


def repo(repo_id, dest, archivos=None, revision='main', patrones=None):
    """Baja archivos de un repositorio de Hugging Face (la lista dada, o los que cumplan los patrones) a la carpeta dest."""
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    if listo(dest):
        return dest
    if archivos is None:
        with _abrir(f'{HF}/api/models/{repo_id}') as r:
            archivos = [s['rfilename'] for s in json.load(r).get('siblings', []) if not s['rfilename'].startswith('.')]
        if patrones:
            archivos = [a for a in archivos if any(fnmatch.fnmatch(a, pt) for pt in patrones)]
    for a in archivos:
        archivo(f'{HF}/{repo_id}/resolve/{revision}/{a}', dest / a, a)
    (dest / 'LISTO.json').write_text(json.dumps({'repo': repo_id, 'revision': revision, 'archivos': archivos}, ensure_ascii=False), encoding='utf-8')
    return dest


def listo(dest):
    return (Path(dest) / 'LISTO.json').exists()


if __name__ == '__main__':
    import sys
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    archivo(sys.argv[1], sys.argv[2])
