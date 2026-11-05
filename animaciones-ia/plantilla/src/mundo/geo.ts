// Globo ortográfico con costas reales (Natural Earth, dominio público). Sin dependencias.
import GEO from './geo.json';

export const TIERRA = GEO.tierra as number[][][];
export const MEXICO = GEO.mexico as number[][][];
export const CHINA = GEO.china as number[][][];

const RAD = Math.PI / 180;
export type V3 = [number, number, number];
export type Vista = { lat: number; lon: number; rol: number };

export const crearVista = (v: Vista) => {
  const sf = Math.sin(v.lat * RAD); const cf = Math.cos(v.lat * RAD);
  const sr = Math.sin(v.rol * RAD); const cr = Math.cos(v.rol * RAD);
  // x a la derecha, y hacia arriba, z hacia quien mira
  return (la: number, lo: number): V3 => {
    const p = la * RAD; const l = (lo - v.lon) * RAD;
    const cp = Math.cos(p); const sp = Math.sin(p);
    const x = cp * Math.sin(l);
    const y = cf * sp - sf * cp * Math.cos(l);
    const z = sf * sp + cf * cp * Math.cos(l);
    return [x * cr - y * sr, x * sr + y * cr, z];
  };
};

const f = (n: number) => n.toFixed(1);

const EPS = 1e-9;
const VUELTA = 2 * Math.PI;
const igual = (a: V3, b: V3) => Math.abs(a[0] - b[0]) < EPS && Math.abs(a[1] - b[1]) < EPS && Math.abs(a[2] - b[2]) < EPS;

// Quita puntos repetidos y antenas (ida y vuelta por el mismo camino): la Antártida baja al polo por el meridiano 180 y regresa por él.
// En la esfera esa antena no encierra nada, y sus dos cruces con la orilla caerían en el mismo punto.
const limpiar = (pts: V3[]): V3[] => {
  const s: V3[] = [];
  for (const p of pts) {
    if (s.length && igual(s[s.length - 1], p)) continue;
    if (s.length > 1 && igual(s[s.length - 2], p)) { s.pop(); continue; }
    s.push(p);
  }
  while (s.length > 2) {
    if (igual(s[0], s[s.length - 1])) s.pop();
    else if (igual(s[1], s[s.length - 1])) s.shift();
    else if (igual(s[0], s[s.length - 2])) s.pop();
    else break;
  }
  return s;
};

// Ángulo sólido con signo, en su lado menor (todo continente cabe en un hemisferio). Positivo = antihorario visto desde afuera.
// Se mide sobre los puntos ya proyectados porque un mapa como la antípoda invierte el sentido del anillo.
const areaConSigno = (p: V3[]): number => {
  const a = p[0]; let s = 0;
  for (let i = 1; i < p.length - 1; i++) {
    const b = p[i]; const c = p[i + 1];
    const num = a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) + a[2] * (b[0] * c[1] - b[1] * c[0]);
    const den = 1 + a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + b[0] * c[0] + b[1] * c[1] + b[2] * c[2] + c[0] * a[0] + c[1] * a[1] + c[2] * a[2];
    s += 2 * Math.atan2(num, den);
  }
  return s - 2 * VUELTA * Math.round(s / (2 * VUELTA));
};

// Punto donde la arista a→b cruza la orilla (z = 0), como ángulo sobre el limbo.
const cruce = (a: V3, b: V3): number => {
  const t = a[2] / (a[2] - b[2]);
  return Math.atan2(a[1] + t * (b[1] - a[1]), a[0] + t * (b[0] - a[0]));
};

type Tramo = { p: V3[]; ini: number; fin: number };

// Polígono al globo: se recorta contra el hemisferio visible. Cada tramo que sale por la orilla se une con el siguiente que entra,
// siguiendo el arco del limbo en el sentido del anillo, para que el interior quede del mismo lado.
export const anillo = (r: number[][], V: (la: number, lo: number) => V3, cx: number, cy: number, R: number, mapa?: (la: number, lo: number) => [number, number]): string => {
  const pts = limpiar(r.map(([lo0, la0]) => { const [la, lo] = mapa ? mapa(la0, lo0) : [la0, lo0]; return V(la, lo); }));
  const n = pts.length;
  if (n < 3) return '';
  const X = (x: number) => f(cx + x * R);
  const Y = (y: number) => f(cy - y * R);

  let arranque = -1; let hayFrente = false;
  for (let i = 0; i < n; i++) {
    if (pts[i][2] >= 0) hayFrente = true;
    else if (pts[(i + 1) % n][2] >= 0) arranque = i; // de atrás hacia el frente
  }
  if (!hayFrente) return ''; // todo atrás: el lado menor queda atrás también
  if (arranque < 0) return `${pts.map((p, i) => `${i ? 'L' : 'M'}${X(p[0])},${Y(p[1])}`).join('')}Z`; // todo al frente

  const tramos: Tramo[] = [];
  let tr: Tramo | null = null;
  for (let k = 0; k < n; k++) {
    const a = pts[(arranque + k) % n]; const b = pts[(arranque + k + 1) % n];
    if (a[2] < 0 && b[2] >= 0) { tr = { p: [b], ini: cruce(a, b), fin: 0 }; continue; }
    if (!tr) continue;
    if (b[2] >= 0) tr.p.push(b);
    else { tr.fin = cruce(a, b); tramos.push(tr); tr = null; }
  }

  const horario = areaConSigno(pts) < 0;
  const dist = (de: number, a: number) => { const d = (horario ? de - a : a - de) % VUELTA; return d < 0 ? d + VUELTA : d; };
  const usado = tramos.map(() => false);
  let d = '';
  for (let i0 = 0; i0 < tramos.length; i0++) {
    if (usado[i0]) continue;
    let i = i0;
    d += `M${X(Math.cos(tramos[i].ini))},${Y(Math.sin(tramos[i].ini))}`;
    for (;;) {
      usado[i] = true;
      const t = tramos[i];
      for (const p of t.p) d += `L${X(p[0])},${Y(p[1])}`;
      d += `L${X(Math.cos(t.fin))},${Y(Math.sin(t.fin))}`;
      // siguiente entrada sobre el limbo
      let sig = 0; let min = Infinity;
      tramos.forEach((o, j) => { const q = dist(t.fin, o.ini); if (q < min) { min = q; sig = j; } });
      // arco en pedazos de hasta un cuarto de vuelta: con redondeo, un arco casi completo dejaría de dibujarse
      const pedazos = Math.ceil(min / (VUELTA / 4));
      for (let k = 1; k <= pedazos; k++) {
        const th = t.fin + (horario ? -1 : 1) * (min * k) / pedazos;
        d += `A${f(R)},${f(R)} 0 0 ${horario ? 1 : 0} ${X(Math.cos(th))},${Y(Math.sin(th))}`;
      }
      if (sig === i0 || usado[sig]) break;
      i = sig;
    }
    d += 'Z';
  }
  return d;
};

export const poligonos = (P: number[][][], V: (la: number, lo: number) => V3, cx: number, cy: number, R: number, mapa?: (la: number, lo: number) => [number, number]) =>
  P.map((r) => anillo(r, V, cx, cy, R, mapa)).join('');

// Línea por el frente del globo; los tramos de atrás se saltan. hasta = 0–1 la va dibujando.
export const linea = (n: number, punto: (i: number) => [number, number], V: (la: number, lo: number) => V3, cx: number, cy: number, R: number, hasta = 1): string => {
  let d = ''; let pluma = false;
  const fin = Math.floor(n * hasta);
  for (let i = 0; i <= fin; i++) {
    const [la, lo] = punto(i);
    const [x, y, z] = V(la, lo);
    if (z < 0) { pluma = false; continue; }
    d += `${pluma ? 'L' : 'M'}${f(cx + x * R)},${f(cy - y * R)}`;
    pluma = true;
  }
  return d;
};

// Círculo pequeño sobre la esfera, de radio dado en km alrededor de un punto.
export const circuloKm = (la0: number, lo0: number, km: number, n = 90): ((i: number) => [number, number]) => {
  const c = km / 6371; const p0 = la0 * RAD;
  return (i) => {
    const b = (i / n) * 2 * Math.PI;
    const la = Math.asin(Math.sin(p0) * Math.cos(c) + Math.cos(p0) * Math.sin(c) * Math.cos(b));
    const lo = lo0 * RAD + Math.atan2(Math.sin(b) * Math.sin(c) * Math.cos(p0), Math.cos(c) - Math.sin(p0) * Math.sin(la));
    return [la / RAD, lo / RAD];
  };
};
