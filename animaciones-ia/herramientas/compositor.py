"""Música ORIGINAL sintetizada nota por nota con numpy: sin samples, sin bancos de sonido y sin pistas de terceros.
Así ningún sistema de derechos (Content ID / Rights Manager) tiene un archivo de referencia con qué compararla:
las pistas «libres» muy usadas sí pueden traer reclamos automáticos.

Estilo: trap épico (808, clap, hi-hats con redobles, pad oscuro, campana y metales sintéticos), en menor.
Uso como librería:
    from compositor import Cancion
    c = Cancion(semilla=1234, bpm=140, tono='D', dur=30.0)
    c.seccion(0, 4, 'intro'); c.seccion(4, 24, 'drop'); c.seccion(24, 30, 'final')
    estereo = c.render()          # np.float32 (n, 2) a 48 kHz
Por línea de comandos, mejor usa:  python ia.py musica --dur 30 --salida musica.wav
Cada pieza depende de su semilla: la misma semilla da exactamente el mismo audio (guárdala: es tu prueba de autoría).
"""
import argparse, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
NOTAS = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
MENOR = [0, 2, 3, 5, 7, 8, 10]
# progresiones en grados de la escala menor (i, VI, III, VII…): cada canción elige una por semilla
PROGRESIONES = [[0, 5, 2, 6], [0, 5, 3, 4], [0, 3, 5, 4], [0, 6, 5, 4], [0, 5, 6, 4]]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def lp(x, f, orden=2):
    return sosfilt(butter(orden, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x).astype(np.float32)


def hp(x, f, orden=2):
    return sosfilt(butter(orden, f, 'high', fs=SR, output='sos'), x).astype(np.float32)


def bp(x, a, b):
    return sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x).astype(np.float32)


def env(n, a=0.002, d=0.2, s=0.0, r=0.05, largo=None):
    """ADSR en muestras; largo = duración de la nota sostenida (s)."""
    t = np.arange(n) / SR
    largo = largo if largo is not None else n / SR
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
    e = np.where(t > largo, e * np.exp(-(t - largo) / max(r, 1e-6)), e)
    return e.astype(np.float32)


def saw(f, n, fase=0.0):
    t = np.arange(n) / SR
    return (2 * ((f * t + fase) % 1.0) - 1).astype(np.float32)


def suave(x, ent=0.002, sal=0.03):
    """Rampa de entrada y salida en cada nota: sin clics al cortar el búfer."""
    x = x.copy(); a, b = int(ent * SR), int(sal * SR)
    if len(x) > a + b:
        x[:a] *= np.linspace(0, 1, a, dtype=np.float32)[:, None] if x.ndim == 2 else np.linspace(0, 1, a, dtype=np.float32)
        x[-b:] *= np.linspace(1, 0, b, dtype=np.float32)[:, None] if x.ndim == 2 else np.linspace(1, 0, b, dtype=np.float32)
    return x


# ---------------- instrumentos ----------------
def i_808(f, dur, rng):
    n = int((dur + 0.6) * SR); t = np.arange(n) / SR
    caida = f * (1 + 1.8 * np.exp(-t / 0.025))            # golpe de tono al inicio
    x = np.sin(2 * np.pi * np.cumsum(caida) / SR)
    x = np.tanh(2.2 * x) * env(n, 0.001, 0.9, 0.55, 0.12, dur)
    return x.astype(np.float32)


def i_kick(rng):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 140 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    clic = hp(rng.standard_normal(n).astype(np.float32), 3000) * np.exp(-t / 0.004) * 0.3
    return np.tanh(1.6 * (x + clic)).astype(np.float32)


def i_clap(rng):
    n = int(0.4 * SR); t = np.arange(n) / SR
    ruido = bp(rng.standard_normal(n).astype(np.float32), 900, 5000)
    e = sum(np.exp(-np.clip(t - k * 0.011, 0, None) / 0.008) * (t >= k * 0.011) for k in range(3)) + 0.9 * np.exp(-np.clip(t - 0.03, 0, None) / 0.11) * (t >= 0.03)
    cuerpo = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.35
    return (ruido * e * 0.8 + cuerpo).astype(np.float32)


def i_hat(rng, abierto=False):
    n = int((0.35 if abierto else 0.06) * SR); t = np.arange(n) / SR
    # metálico: suma de cuadradas en razones inarmónicas + ruido, pasa-altos
    x = sum(np.sign(np.sin(2 * np.pi * f0 * t)) for f0 in (3150, 4420, 5310, 6870, 8140, 9530)) / 6
    x = hp((x + 0.6 * rng.standard_normal(n)).astype(np.float32), 7000, 4)
    return (x * np.exp(-t / (0.12 if abierto else 0.018))).astype(np.float32)


def i_pad(fs, dur, rng):
    n = int((dur + 2.6) * SR)
    x = np.zeros(n, np.float32)
    for f in fs:
        for det in (-0.12, 0.0, 0.11):
            x += saw(f * 2 ** (det / 12), n, rng.random())
    x = lp(x / (3 * len(fs)), 1400, 2)
    return (x * env(n, 0.6, 1.0, 0.8, 0.9, dur)).astype(np.float32)


def i_campana(f, dur, rng):
    n = int((dur + 2.5) * SR); t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.4 * np.exp(-t / 0.35)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.9)
    return (x * env(n, 0.002, 2.0, 0.0, 0.3, dur)).astype(np.float32)


def i_metal(fs, dur, rng):  # metales sintéticos (stab épico)
    n = int((dur + 1.2) * SR)
    x = np.zeros(n, np.float32)
    for f in fs:
        for det in (-0.07, 0.07):
            x += saw(f * 2 ** (det / 12), n, rng.random())
    corte = 600 + 3800 * env(n, 0.02, 0.25, 0.25, 0.2, dur)
    y = np.zeros(n, np.float32)
    for k in range(0, n, 512):  # filtro que se abre y se cierra (por bloques)
        y[k:k + 512] = lp(x[max(0, k - 2048):k + 512], float(corte[k]))[-len(x[k:k + 512]):]
    return (np.tanh(1.4 * y / len(fs)) * env(n, 0.015, 0.4, 0.6, 0.25, dur)).astype(np.float32)


def reverb(x, seg=2.2, mezcla=0.25, semilla=0):
    rng = np.random.default_rng(semilla)
    n = int(seg * SR); t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n) * np.exp(-t / (seg / 6.5)) for _ in range(2)], 1).astype(np.float32)
    ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
    ir /= np.sqrt((ir ** 2).sum(0))
    mojado = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1).astype(np.float32)
    return x * (1 - mezcla) + mojado * mezcla


class Cancion:
    def __init__(self, semilla=1, bpm=140, tono='D', dur=60.0):
        self.rng = np.random.default_rng(semilla)
        self.bpm, self.raiz, self.dur = bpm, 48 + NOTAS[tono], dur
        self.beat = 60 / bpm
        self.prog = PROGRESIONES[self.rng.integers(len(PROGRESIONES))]
        self.secciones = []
        self.motivo = self._motivo()

    def seccion(self, t0, t1, tipo):
        self.secciones.append((t0, t1, tipo))

    def _grado(self, g, octava=0):
        return self.raiz + MENOR[g % 7] + 12 * (g // 7 + octava)

    def _motivo(self):  # melodía de 2 compases (16 corcheas) que se repite y varía: grados de la escala o silencio
        m = []
        for k in range(16):
            if k % 4 == 0 or self.rng.random() < 0.45:
                m.append(int(self.rng.choice([0, 2, 4, 4, 3, 6, 7, 5])))
            else:
                m.append(None)
        return m

    def render(self):
        n = int((self.dur + 2) * SR)
        bat = np.zeros((n, 2), np.float32); bajo = np.zeros(n, np.float32)
        pad = np.zeros((n, 2), np.float32); mel = np.zeros((n, 2), np.float32)
        b, rng = self.beat, self.rng
        kick, clap = i_kick(rng), i_clap(rng)
        hats = [i_hat(rng) for _ in range(4)]; hat_ab = i_hat(rng, True)

        def suma(dst, x, t, g=1.0, pan=0.0):
            x = suave(x)
            i = int(t * SR); m = min(len(x), n - i)
            if m <= 0 or i < 0: return
            if dst.ndim == 1: dst[i:i + m] += x[:m] * g
            else:
                dst[i:i + m, 0] += x[:m] * g * (1 - max(0, pan)); dst[i:i + m, 1] += x[:m] * g * (1 + min(0, pan))

        compas = 4 * b
        for (t0, t1, tipo) in self.secciones:
            c = 0
            tc = t0
            while tc < t1 - 1e-6:
                acorde = self.prog[c % len(self.prog)]
                fs = [hz(self._grado(acorde + k, 0)) for k in (0, 2, 4)]
                largo = min(compas, t1 - tc)
                # pad: siempre (más suave en el drop)
                p = i_pad(fs, largo, rng)
                suma(pad, p, tc, 0.55 if tipo in ('intro', 'tension') else 0.38, -0.3); suma(pad, p, tc + 0.012, 0.55 if tipo in ('intro', 'tension') else 0.38, 0.3)
                if tipo in ('drop', 'final'):
                    # 808 siguiendo la raíz del acorde, patrón trap (1, 1.75, 2.5 | 3.5)
                    for pos, d in ((0, 0.7), (1.75, 0.5), (2.5, 0.9), (3.5, 0.4)):
                        if tc + pos * b < t1:
                            suma(bajo, i_808(hz(self._grado(acorde, -1)), d * b, rng), tc + pos * b, 0.62)
                    for pos in (0, 2.5):
                        suma(bat, kick, tc + pos * b, 0.75)
                    for pos in (1, 3):
                        suma(bat, clap, tc + pos * b, 0.55)
                    # hi-hats en corcheas con redobles (1/16 y tresillos) al final del compás
                    k = 0.0
                    while k < 4:
                        rodar = k >= 3 and (c % 2 == 1)
                        paso = (1 / 6 if rng.random() < 0.5 else 1 / 4) if rodar else 0.5
                        suma(bat, hats[int(rng.integers(4))], tc + k * b, 0.22 + 0.06 * rng.random(), 0.35)
                        k += paso
                    if c % 4 == 3:
                        suma(bat, hat_ab, tc + 3.5 * b, 0.16, 0.35)
                    # melodía de campana
                    for j, g in enumerate(self.motivo[(c % 2) * 8:(c % 2) * 8 + 8]):
                        if g is not None and tc + j * b / 2 < t1:
                            suma(mel, i_campana(hz(self._grado(acorde + g, 1)), b / 2, rng), tc + j * b / 2, 0.16, -0.2 + 0.4 * (j % 2))
                    if tipo == 'final' or c % 4 == 0:  # golpe de metales al empezar cada frase
                        suma(mel, i_metal([hz(self._grado(acorde + k2, 0)) for k2 in (0, 2, 4, 7)], 1.2 * b, rng), tc, 0.30)
                elif tipo == 'tension':
                    # latido grave en negras que se acelera y redoble de hats
                    for pos in range(4):
                        suma(bajo, i_808(hz(self._grado(0, -1)), 0.35 * b, rng), tc + pos * b, 0.45)
                    for pos in np.arange(0, 4, 0.25):
                        suma(bat, hats[int(rng.integers(4))], tc + pos * b, 0.12 + 0.03 * pos, 0.3)
                else:  # intro: pad + campana suelta + hats tenues
                    for j, g in enumerate(self.motivo[:8]):
                        if g is not None and j % 2 == 0:
                            suma(mel, i_campana(hz(self._grado(acorde + g, 1)), b, rng), tc + j * b / 2, 0.12)
                    for pos in np.arange(0, 4, 0.5):
                        suma(bat, hats[int(rng.integers(4))], tc + pos * b, 0.08, 0.3)
                tc += compas; c += 1

        mezcla = bat + np.stack([bajo, bajo], 1) + reverb(pad, 2.8, 0.35, 1) + reverb(mel, 2.2, 0.3, 2)
        mezcla = hp(mezcla.T, 28).T  # quita subgraves inaudibles
        mezcla = np.tanh(1.1 * mezcla) / 1.1
        mezcla = mezcla[:int(self.dur * SR)]
        return (mezcla / max(1e-6, np.abs(mezcla).max()) * 0.89).astype(np.float32)


def victoria(semilla=3, tono='D', dur=2.6):
    """Golpe + acorde mayor de metales que sube (para el campeón). Original."""
    rng = np.random.default_rng(semilla)
    raiz = 48 + NOTAS[tono]
    n = int(dur * SR)
    x = np.zeros((n, 2), np.float32)
    k = i_kick(rng)[:n]; x[:len(k)] += np.stack([k, k], 1) * 0.9
    for i, (st, fs) in enumerate([(0.0, [0, 4, 7]), (0.18, [2, 7, 11]), (0.36, [4, 7, 12, 16])]):
        m = i_metal([hz(raiz + 12 + s) for s in fs], 0.9 if i == 2 else 0.16, rng)
        j = int(st * SR); l = min(len(m), n - j)
        x[j:j + l] += np.stack([m[:l], m[:l]], 1) * 0.5
    c = i_campana(hz(raiz + 28), 1.5, rng)[:n - int(0.36 * SR)]
    x[int(0.36 * SR):int(0.36 * SR) + len(c)] += np.stack([c, c], 1) * 0.25
    x = reverb(x, 2.0, 0.3, 5)
    return (x / np.abs(x).max() * 0.9).astype(np.float32)


def golpe(semilla=4):
    """Impacto grave original (sustituye jingles de terceros)."""
    rng = np.random.default_rng(semilla)
    n = int(0.9 * SR); t = np.arange(n) / SR
    k = i_kick(rng); x = np.zeros(n, np.float32); x[:len(k)] += k
    x += lp(rng.standard_normal(n).astype(np.float32), 2500) * np.exp(-t / 0.15) * 0.4
    x += np.sin(2 * np.pi * 45 * t) * np.exp(-t / 0.35) * 0.7
    x = np.tanh(1.5 * x)
    return np.stack([x, x], 1).astype(np.float32) / 1.2


def guardar(x, ruta):
    crudo = str(ruta) + '.f32'
    x.astype(np.float32).tofile(crudo)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', crudo, '-c:a', 'pcm_s24le', str(ruta)], check=True)
    import os; os.remove(crudo)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('salida'); a.add_argument('--dur', type=float, default=40); a.add_argument('--semilla', type=int, required=True)
    a.add_argument('--bpm', type=float, default=140); a.add_argument('--tono', default='D')
    o = a.parse_args()
    c = Cancion(o.semilla, o.bpm, o.tono, o.dur)
    c.seccion(0, 4 * c.beat * 2, 'intro'); c.seccion(4 * c.beat * 2, o.dur - 6, 'drop'); c.seccion(o.dur - 6, o.dur, 'final')
    guardar(c.render(), o.salida)
    print('listo', o.salida)
