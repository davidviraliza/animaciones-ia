// Ayudas de dibujo, para quien las quiera: azar fijo por índice, mezcla de color, rectángulo redondeado y trazo con desregistro.
import React from 'react';
import { cl, lerp } from './curvas';
import { EstiloTrazo } from './estilo';

export const rnd = (i: number) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
export const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const mezclar = (a: string, b: string, k: number) => {
  const A = hex(a); const B = hex(b);
  return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], cl(k)))).join(',')})`;
};
export const rr = (x: number, y: number, w: number, h: number, r = 0) =>
  `M${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x + r}Q${x},${y + h} ${x},${y + h - r}V${y + r}Q${x},${y} ${x + r},${y}Z`;

// Trazo: la tinta de color va corrida respecto a la línea, según estilo.trazo.
export const crearTrazo = (e: EstiloTrazo): React.FC<{ d: string; fill: string; sw?: number; linea?: string }> => {
  const { dx, dy } = e.desregistro ?? { dx: 0, dy: 0 };
  return ({ d, fill, sw = e.grosor ?? 5, linea = e.linea }) => (
    <g>
      <path d={d} fill={fill} transform={`translate(${dx},${dy})`} />
      <path d={d} fill="none" stroke={linea} strokeWidth={sw} strokeLinejoin="round" />
    </g>
  );
};
