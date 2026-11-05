// Una sola capa de texto: palabra por palabra, según los tiempos de la voz. Sin cajas, sin sombra, sin contorno.
import React from 'react';
import { sale } from './curvas';
import { Estilo } from './estilo';
import { fuenteLista, useFuente } from './fuente';
import { FraseVoz, TiemposVoz, norm } from './voz';

type E = Estilo<unknown>;
const sinAcento = (c: string) => c.normalize('NFD')[0];
const medidas = new Map<string, number>();

// Ancho de una línea en em, medido con un elemento oculto ya con la fuente cargada.
const medirEm = (l: string, e: E) => {
  const f = e.fuente;
  if (typeof document === 'undefined' || !fuenteLista(f)) return [...l].length * 0.5;
  const clave = `${f?.familia}|${f?.variacion}|${l}`;
  const ya = medidas.get(clave);
  if (ya !== undefined) return ya;
  const n = document.createElement('span');
  n.textContent = l;
  Object.assign(n.style, {
    position: 'absolute', visibility: 'hidden', whiteSpace: 'pre', fontSize: '100px',
    fontFamily: `${f?.familia ?? 'sans-serif'}, sans-serif`, fontVariationSettings: f?.variacion ?? 'normal', fontWeight: String(f?.pesoCss ?? 400),
  });
  document.body.appendChild(n);
  const w = n.getBoundingClientRect().width / 100;
  document.body.removeChild(n);
  medidas.set(clave, w);
  return w;
};

// De centro de línea a línea base, en em: depende de la fuente, así que se mide con un marcador sobre la línea base.
const medirBase = (e: E) => {
  const f = e.fuente;
  if (typeof document === 'undefined' || !fuenteLista(f)) return 0.3;
  const clave = `base|${f?.familia}|${f?.variacion}`;
  const ya = medidas.get(clave);
  if (ya !== undefined) return ya;
  const n = document.createElement('div');
  Object.assign(n.style, {
    position: 'absolute', visibility: 'hidden', top: '0', fontSize: '100px', lineHeight: '100px',
    fontFamily: `${f?.familia ?? 'sans-serif'}, sans-serif`, fontVariationSettings: f?.variacion ?? 'normal', fontWeight: String(f?.pesoCss ?? 400),
  });
  n.textContent = 'H';
  const marca = document.createElement('span');
  marca.style.display = 'inline-block';
  n.appendChild(marca);
  document.body.appendChild(n);
  const b = (marca.getBoundingClientRect().bottom - n.getBoundingClientRect().top - 50) / 100;
  document.body.removeChild(n);
  medidas.set(clave, b);
  return b;
};

// Cuánto baja de la línea base esta línea en concreto (J, Q, comas…), en em.
const descensoEm = (l: string, e: E) => {
  const f = e.fuente;
  if (typeof document === 'undefined' || !fuenteLista(f)) return 0;
  const clave = `baja|${f?.familia}|${l}`;
  const ya = medidas.get(clave);
  if (ya !== undefined) return ya;
  const ctx = document.createElement('canvas').getContext('2d');
  if (!ctx) return 0;
  ctx.font = `${f?.pesoCss ?? 400} 100px ${f?.familia ?? 'sans-serif'}, sans-serif`;
  const d = Math.max(0, ctx.measureText(l).actualBoundingBoxDescent) / 100;
  medidas.set(clave, d);
  return d;
};

export const anchoEm = (l: string, e: E) => {
  const av = e.texto.avances;
  return av ? [...l].reduce((s, c) => s + (av[sinAcento(c)] ?? e.texto.avanceOtro ?? 0.5), 0) : medirEm(l, e);
};

const tieneCola = (l: string, e: E) => !!e.texto.cola && [...e.texto.cola.letras].some((c) => l.includes(c));

export const tamano = (lineas: string[], liga: boolean, e: E) => {
  const x = e.texto;
  const conCola = !liga && lineas.length === 1 && tieneCola(lineas[0], e);
  const tope = lineas.length > 1 ? x.topeDos : conCola ? x.cola!.tope : liga ? x.topeLiga : x.topeUna;
  return Math.min(tope, x.anchoMax / Math.max(...lineas.map((l) => anchoEm(l, e))));
};

export const Palabra: React.FC<{
  lineas: string[];
  estilo: E;
  pieza?: boolean; // true = nombre de pieza, en su color
  liga?: boolean; // true = palabra de enlace, más chica
  centroY?: number; // centro del bloque; por omisión asienta en texto.yPie
  golpe?: number; // 0–1, resorte de entrada
}> = ({ lineas, estilo, pieza = false, liga = false, centroY, golpe = 1 }) => {
  useFuente(estilo.fuente);
  const x = estilo.texto;
  const f = estilo.fuente;
  const fs = tamano(lineas, liga, estilo);
  // Toda palabra asienta en la misma línea, sin importar su tamaño.
  const lh = lineas.length > 1 ? x.altoLineaDos : x.altoLinea;
  // Con la métrica a mano, se usa tal cual; sin ella, se mide con la fuente del video, y el texto no se sale de la zona con ninguna.
  const cola = x.bajoCentro === undefined ? descensoEm(lineas[lineas.length - 1], estilo) * fs : x.cola && lineas.some((l) => tieneCola(l, estilo)) ? x.cola.fraccion * fs : 0;
  const bajoCentro = (x.bajoCentro ?? medirBase(estilo)) * fs + ((lineas.length - 1) * lh * fs) / 2;
  const y = centroY ?? x.yPie - cola - bajoCentro;
  const alto = lineas.length * lh * fs;
  const escala = x.escalaEntrada + (1 - x.escalaEntrada) * golpe; // crece desde la línea base: no se sale de la zona
  return (
    <div style={{
      position: 'absolute', left: 0, width: 1080, top: y, transform: `translateY(-50%) scale(${escala})`, transformOrigin: `50% ${alto / 2 + bajoCentro}px`, textAlign: 'center',
      fontFamily: `${f?.familia ?? 'sans-serif'}, sans-serif`, fontVariationSettings: f?.variacion, fontWeight: f?.pesoCss,
      fontSize: fs, lineHeight: lh, color: pieza ? x.colorPieza : x.color, opacity: golpe > 0 ? 1 : 0,
    }}>
      {lineas.map((l) => <div key={l}>{l}</div>)}
    </div>
  );
};

// Guía opcional, una entrada por frase: palabras clave, nombre de pieza (lineas) y palabra en la que entra.
export type GuiaFrase = { palabras?: string[]; pieza?: string[] | null; golpe?: string };
export type Letrero = { t0: number; lineas: string[]; pieza: boolean; clave: boolean };

export const crearLetreros = (T: TiemposVoz, guia: GuiaFrase[] | undefined, o: { estilo: E; soloNombre?: (i: number) => boolean; fps?: number }) => {
  const fps = o.fps ?? 30;
  const soloNombre = o.soloNombre ?? (() => false);
  const letreros: Letrero[] = [];
  T.frases.forEach((f: FraseVoz, i: number) => {
    const g = guia?.[i];
    const claves = g?.palabras ? new Set(g.palabras.map(norm)) : null; // sin guía, todas son clave
    for (const p of f.palabras) {
      const n = norm(p.w);
      if (g?.pieza && n === norm(g.golpe ?? '')) { letreros.push({ t0: p.s, lineas: g.pieza, pieza: true, clave: true }); break; }
      if (soloNombre(i)) continue; // esa frase solo muestra el nombre
      letreros.push({ t0: i === 0 && p === f.palabras[0] ? 0 : p.s, lineas: [p.w.replace(/[.,;:¿?¡!]/g, '').toUpperCase()], pieza: false, clave: claves ? claves.has(n) : true });
    }
    // la palabra anterior se quita al empezar una frase de solo nombre
    if (i + 1 < T.frases.length && soloNombre(i + 1)) letreros.push({ t0: T.frases[i + 1].ini, lineas: [], pieza: false, clave: false });
  });
  letreros.sort((x, y) => x.t0 - y.t0);

  const Texto: React.FC<{ t: number }> = ({ t }) => {
    let l: Letrero | null = null;
    for (const x of letreros) { if (t + 1 / (2 * fps) >= x.t0) l = x; else break; }
    if (!l || l.lineas.length === 0) return null;
    const c = (t - l.t0) * fps + 0.5; // cuadros desde que entró
    const golpe = l.clave ? sale((c + 1) / 4) : sale((c + 1) / 2);
    return <Palabra key={l.t0} lineas={l.lineas} estilo={o.estilo} pieza={l.pieza} liga={!l.clave} golpe={golpe} />;
  };
  return { letreros, Texto };
};
