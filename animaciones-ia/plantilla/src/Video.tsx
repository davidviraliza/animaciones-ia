// Línea de tiempo del video. NO hace falta editar este archivo: todo sale de escenas.json (qué se ve en cada frase) y tiempos.json (cuándo dice la voz cada palabra).
// Escenas: «globo» (gira, se acerca, pines, rutas), «contador» (número que corre con la voz) y «palabra» (campo de puntos con ondas en los golpes).
// Texto: una sola capa, palabra por palabra al ritmo de la voz; las claves van grandes y en color de acento.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import T0 from './tiempos.json';
import ESC from './escenas.json';
import { crearLetreros, crearPistas, crearTiempos, crearVideo, FraseVoz, norm, Palabra, sale, lineal, TiemposVoz } from './motor';
import { crearEstilo } from './estilo';
import { Globo, Punto, Ruta } from './mundo/Globo';
import { Anillo, Campo } from './mundo/Fondos';

type Vista = { lat: number; lon: number; zoom?: number };
type Contador = { desde?: number; hasta: number; unidad?: string; inicia?: string; termina?: string; decimales?: number };
type Escena = {
  id: string;
  escena?: 'globo' | 'contador' | 'palabra';
  corte?: boolean; // true = corte seco al empezar la frase aunque la escena no cambie
  vista?: Vista; // globo: a dónde gira (lat, lon) y cuánto se acerca (zoom 1 = globo entero)
  puntos?: { lat: number; lon: number; en?: string }[]; // pines; «en» = palabra en la que aparecen
  ruta?: { de: [number, number]; a: [number, number]; desde?: string; hasta?: string };
  claves?: string[]; // palabras que salen grandes y en color
  golpe?: string; // palabra en la que la cámara da un brinco (y el giro del globo llega)
  contador?: Contador;
  juntar?: [string, string][]; // [lo que dice la voz, lo que sale en pantalla]: «doce mil metros» → «12,000 M»
};

const T = T0 as TiemposVoz;
const E = ESC as { paleta?: string; frases: Escena[] };
const { paleta: P, estilo: ESTILO } = crearEstilo(E.paleta ?? 'noche');
const { I, F, W: W0 } = crearTiempos(T);
// Si una palabra de escenas.json no está en la voz, se usa el inicio de la frase en vez de romper el render.
const W = (id: string, palabra?: string, alFinal = false) => {
  if (!palabra) return alFinal ? F(id) : I(id);
  try { return W0(id, palabra.split(' ')[0]); } catch { console.warn(`escenas.json: no está «${palabra}» en ${id}`); return alFinal ? F(id) : I(id); }
};

const FR = T.frases.map((f) => ({ f, e: E.frases.find((x) => x.id === f.id) ?? ({ id: f.id } as Escena) }));
const tipos: NonNullable<Escena['escena']>[] = [];
FR.forEach(({ e }, i) => tipos.push(e.escena ?? tipos[i - 1] ?? 'globo'));
const corte = (i: number) => (i === 0 ? 0 : I(FR[i].f.id) - 0.03); // el corte cae justo antes de la voz
const nuevaToma = FR.map(({ e }, i) => i === 0 || tipos[i] !== tipos[i - 1] || !!e.corte);
const finToma = (i: number) => { for (let k = i + 1; k < FR.length; k++) if (nuevaToma[k]) return corte(k); return T.dur + 1; };
const inicioToma = (t: number) => { let s = 0; FR.forEach((_, i) => { if (nuevaToma[i] && corte(i) <= t) s = corte(i); }); return s; };
const frase = (t: number) => { let k = 0; FR.forEach((_, i) => { if (corte(i) <= t) k = i; }); return k; };

// ---------- globo: giro y acercamiento por pistas ----------
const primera = E.frases.find((x) => x.vista)?.vista ?? { lat: 19.4, lon: -99.1, zoom: 1 };
const { a, estado: pistas } = crearPistas({ lat: primera.lat, lon: primera.lon, zoom: primera.zoom ?? 1 });
let lonAntes = primera.lon;
const puntos: (Punto & { t0: number; t1: number })[] = [];
const rutas: (Omit<Ruta, 'k'> & { t0: number; t1: number; fin: number })[] = [];
const golpes: number[] = [];
const contadores: (Contador & { t0: number; t1: number; fin: number })[] = [];
FR.forEach(({ f, e }, i) => {
  if (e.vista && i > 0) {
    // el globo gira por el camino corto
    const lon = lonAntes + ((((e.vista.lon - lonAntes + 180) % 360) + 360) % 360) - 180;
    const t0 = nuevaToma[i] ? corte(i) : I(f.id);
    const t1 = e.golpe ? W(f.id, e.golpe) + 0.2 : F(f.id);
    const d = nuevaToma[i] ? 0 : Math.max(0.4, t1 - t0);
    a('lat', t0, d, e.vista.lat); a('lon', t0, d, lon); a('zoom', t0, d, e.vista.zoom ?? 1);
    lonAntes = lon;
  }
  for (const q of e.puntos ?? []) puntos.push({ lat: q.lat, lon: q.lon, a: 0, t0: q.en ? W(f.id, q.en) - 0.05 : i === 0 ? 0 : I(f.id), t1: finToma(i) });
  if (e.ruta) rutas.push({ de: e.ruta.de, a: e.ruta.a, t0: W(f.id, e.ruta.desde), t1: e.ruta.hasta ? W(f.id, e.ruta.hasta) + 0.25 : e.golpe ? W(f.id, e.golpe) + 0.2 : F(f.id), fin: finToma(i) });
  if (e.golpe) golpes.push(W(f.id, e.golpe));
  if (e.contador) {
    const c = e.contador;
    const t0 = W(f.id, c.inicia);
    const t1 = c.termina ? W(f.id, c.termina) + 0.3 : F(f.id) - 0.1;
    contadores.push({ ...c, t0, t1: Math.max(t0 + 0.3, t1), fin: finToma(i) });
    golpes.push(Math.max(t0 + 0.3, t1));
  }
});
const contadorEn = (t: number) => contadores.find((c) => t >= c.t0 && t < c.fin);
const valorContador = (c: Contador & { t0: number; t1: number }, t: number) => (c.desde ?? 0) + (c.hasta - (c.desde ?? 0)) * sale((t - c.t0) / (c.t1 - c.t0));
const cifra = (n: number, dec = 0) => {
  const [ent, fr] = Math.abs(n).toFixed(dec).split('.');
  return `${n < 0 ? '-' : ''}${ent.replace(/\B(?=(\d{3})+$)/g, ',')}${fr ? `.${fr}` : ''}`;
};

// ---------- cámara viva: empuje lento en cada toma, deriva y brinco en los golpes ----------
const rebote = (t: number) => golpes.reduce((s, g) => { const u = (t - g) / 0.38; return u > 0 && u < 1 ? s + 0.02 * Math.sin(Math.PI * u) * (1 - u) : s; }, 0);
const CX = 540; const CY = 820; // el mundo vive arriba de la franja del texto

type Estado = { t: number };
const Mundo: React.FC<{ e: Estado }> = ({ e: { t } }) => {
  const i = frase(t);
  const tipo = tipos[i];
  const g = pistas(t);
  const escala = Math.exp(0.012 * (t - inicioToma(t))) * (1 + rebote(t));
  const dx = 7 * Math.sin(t * 0.61) + 4 * Math.sin(t * 1.13 + 1); const dy = 5 * Math.sin(t * 0.47 + 0.6);
  const c = contadorEn(t);
  let capa: React.ReactNode;
  if (tipo === 'contador') capa = <Anillo k={c ? lineal((t - c.t0) / (c.t1 - c.t0)) : 0} t={t} p={P} cx={CX} cy={CY - 120} />;
  else if (tipo === 'palabra') capa = <Campo t={t} p={P} golpes={golpes} cx={CX} cy={CY} />;
  else capa = (
    <Globo lat={g.lat} lon={g.lon} R={400 * g.zoom} cx={CX} cy={CY} t={t} p={P}
      puntos={puntos.filter((q) => t < q.t1).map((q) => ({ ...q, a: t < q.t0 ? 0 : sale((t - q.t0) / 0.35) }))}
      rutas={rutas.filter((r) => t >= r.t0 && t < r.fin).map((r) => ({ ...r, k: lineal((t - r.t0) / (r.t1 - r.t0)) }))} />
  );
  return (
    <AbsoluteFill style={{ transform: `translate(${dx}px, ${dy}px) scale(${escala})`, transformOrigin: `${CX}px ${CY}px` }}>
      {capa}
    </AbsoluteFill>
  );
};

// ---------- texto: una sola capa ----------
const juntas: string[][] = [];
const unir = (f: FraseVoz, dice: string, pantalla: string): FraseVoz => {
  const q = dice.split(' ').map(norm);
  const k = f.palabras.findIndex((_, j) => q.every((x, n) => j + n < f.palabras.length && norm(f.palabras[j + n].w) === x));
  if (k < 0) { console.warn(`escenas.json: no está «${dice}» en ${f.id}`); return f; }
  juntas.push(pantalla.split('|'));
  return { ...f, palabras: [...f.palabras.slice(0, k), { ...f.palabras[k], w: `§${juntas.length - 1}`, e: f.palabras[k + q.length - 1].e }, ...f.palabras.slice(k + q.length)] };
};
const frasesTexto = FR.map(({ f, e }) => (e.juntar ?? []).reduce((x, [dice, pantalla]) => unir(x, dice, pantalla), f));
const { letreros } = crearLetreros({ ...T, frases: frasesTexto }, FR.map(({ e }) => ({ palabras: e.claves ?? [] })), { estilo: ESTILO });
for (const l of letreros) {
  const m = l.lineas.length === 1 ? /^§(\d+)$/.exec(l.lineas[0]) : null;
  if (m) { l.lineas = juntas[+m[1]].map((s) => s.toUpperCase()); l.clave = true; }
  if (l.clave) l.pieza = true;
}
const fps = 30;
const Texto: React.FC<{ t: number }> = ({ t }) => {
  const c = contadorEn(t);
  if (c) return <Palabra lineas={[cifra(valorContador(c, t), c.decimales ?? 0), ...(c.unidad ? [c.unidad.toUpperCase()] : [])]} estilo={ESTILO} pieza golpe={sale(((t - c.t0) * fps + 1) / 4)} />;
  let l: (typeof letreros)[number] | null = null;
  for (const x of letreros) { if (t + 1 / (2 * fps) >= x.t0) l = x; else break; }
  if (!l || l.lineas.length === 0) return null;
  const n = (t - l.t0) * fps + 0.5;
  return <Palabra key={l.t0} lineas={l.lineas} estilo={ESTILO} pieza={l.pieza} liga={!l.clave} golpe={l.clave ? sale((n + 1) / 4) : sale((n + 1) / 2)} />;
};

export const { Video, cuadros: CUADROS } = crearVideo({ tiempos: T, estilo: ESTILO, Mundo, estado: (t: number): Estado => ({ t }), Texto });
