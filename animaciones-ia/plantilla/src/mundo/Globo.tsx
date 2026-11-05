// Globo ortográfico con costas reales (Natural Earth, dominio público): retícula, pines que laten y rutas por el camino más corto.
import React from 'react';
import { cl, sale } from '../motor';
import type { Paleta } from '../estilo';
import { circuloKm, crearVista, linea, poligonos, TIERRA } from './geo';

export type Punto = { lat: number; lon: number; a: number }; // a = 0–1, cuánto ha aparecido
export type Ruta = { de: [number, number]; a: [number, number]; k: number }; // k = 0–1, cuánto se ha dibujado

const RAD = Math.PI / 180;
const v3 = (la: number, lo: number) => [Math.cos(la * RAD) * Math.cos(lo * RAD), Math.cos(la * RAD) * Math.sin(lo * RAD), Math.sin(la * RAD)];
// Punto u (0–1) sobre el círculo máximo de A a B.
const arco = (A: [number, number], B: [number, number]) => {
  const a = v3(A[0], A[1]); const b = v3(B[0], B[1]);
  const w = Math.acos(cl(a[0] * b[0] + a[1] * b[1] + a[2] * b[2], -1, 1));
  return (u: number): [number, number] => {
    if (w < 1e-6) return A;
    const s1 = Math.sin((1 - u) * w) / Math.sin(w); const s2 = Math.sin(u * w) / Math.sin(w);
    const x = s1 * a[0] + s2 * b[0]; const y = s1 * a[1] + s2 * b[1]; const z = s1 * a[2] + s2 * b[2];
    return [Math.asin(cl(z, -1, 1)) / RAD, Math.atan2(y, x) / RAD];
  };
};

export const Globo: React.FC<{ lat: number; lon: number; R: number; cx: number; cy: number; t: number; puntos: Punto[]; rutas: Ruta[]; p: Paleta; atenua?: number }> = ({ lat, lon, R, cx, cy, t, puntos, rutas, p, atenua = 0 }) => {
  const V = crearVista({ lat, lon, rol: 0 });
  const tierra = poligonos(TIERRA, V, cx, cy, R);
  // retícula cada 30°
  let ret = '';
  for (let lo = -180; lo < 180; lo += 30) ret += linea(90, (i) => [-90 + i * 2, lo], V, cx, cy, R);
  for (let la = -60; la <= 60; la += 30) ret += linea(180, (i) => [la, -180 + i * 2], V, cx, cy, R);
  const proy = (la: number, lo: number) => { const [x, y, z] = V(la, lo); return { x: cx + x * R, y: cy - y * R, z }; };
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, opacity: 1 - 0.7 * atenua }}>
      <defs>
        <radialGradient id="halo" cx="50%" cy="50%" r="50%">
          <stop offset="80%" stopColor={p.brillo} stopOpacity={0.35} />
          <stop offset="100%" stopColor={p.brillo} stopOpacity={0} />
        </radialGradient>
        <radialGradient id="luz" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity={0.18} />
          <stop offset="100%" stopColor="#000000" stopOpacity={0.35} />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={R * 1.12} fill="url(#halo)" />
      <circle cx={cx} cy={cy} r={R} fill={p.mar} />
      <path d={ret} fill="none" stroke={p.borde} strokeWidth={2} opacity={0.22} />
      <path d={tierra} fill={p.tierra} stroke={p.borde} strokeWidth={2.5} strokeLinejoin="round" />
      {rutas.map((r, i) => {
        const g = arco(r.de, r.a);
        const d = linea(120, (j) => g(j / 120), V, cx, cy, R, cl(r.k));
        const fin = proy(...g(cl(r.k)));
        return (
          <g key={i}>
            <path d={d} fill="none" stroke={p.acento} strokeWidth={8} strokeDasharray="2 22" strokeLinecap="round" />
            {r.k > 0 && r.k < 1 && fin.z > 0 ? <circle cx={fin.x} cy={fin.y} r={12} fill={p.acento} /> : null}
          </g>
        );
      })}
      {puntos.map((q, i) => {
        if (q.a <= 0) return null;
        const c = proy(q.lat, q.lon);
        if (c.z < 0) return null;
        const f = (t * 1.3 + i * 0.37) % 1;
        // anillo en km alrededor del pin: se ve del tamaño correcto aunque el globo esté de lado
        const onda = linea(60, circuloKm(q.lat, q.lon, 150 + 900 * f, 60), V, cx, cy, R);
        return (
          <g key={i} opacity={cl(q.a * 3)}>
            <path d={onda} fill="none" stroke={p.texto} strokeWidth={4} opacity={1 - f} />
            <circle cx={c.x} cy={c.y} r={18 * sale(q.a)} fill={p.acento} stroke={p.fondo} strokeWidth={6} />
          </g>
        );
      })}
      <circle cx={cx} cy={cy} r={R} fill="url(#luz)" />
    </svg>
  );
};
