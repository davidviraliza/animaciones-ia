// Fondos sin globo: el anillo del contador y el campo de puntos de las escenas de palabra. Nunca llevan texto: el texto es una sola capa (Video.tsx).
import React from 'react';
import { cl, rnd, sale } from '../motor';
import type { Paleta } from '../estilo';

// Anillo que se llena con el avance del contador (k = 0–1) y marcas que giran despacio.
export const Anillo: React.FC<{ k: number; t: number; p: Paleta; cx: number; cy: number }> = ({ k, t, p, cx, cy }) => {
  const R = 300;
  const marcas = Array.from({ length: 60 }, (_, i) => {
    const a = (i / 60) * 2 * Math.PI + t * 0.15;
    const largo = i % 5 === 0 ? 38 : 18;
    return `M${cx + Math.cos(a) * (R + 40)},${cy + Math.sin(a) * (R + 40)}L${cx + Math.cos(a) * (R + 40 + largo)},${cy + Math.sin(a) * (R + 40 + largo)}`;
  }).join('');
  const L = 2 * Math.PI * R;
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke={p.borde} strokeWidth={26} opacity={0.18} />
      <circle cx={cx} cy={cy} r={R} fill="none" stroke={p.acento} strokeWidth={26} strokeLinecap="round"
        strokeDasharray={`${L * cl(k)} ${L}`} transform={`rotate(-90 ${cx} ${cy})`} />
      <path d={marcas} stroke={p.texto} strokeWidth={5} opacity={0.5} />
      <circle cx={cx} cy={cy} r={R * 0.62 * (0.9 + 0.1 * sale(k))} fill={p.mar} opacity={0.55} />
    </svg>
  );
};

// Campo de puntos que deriva, con una onda que sale del centro en cada golpe (golpes = tiempos en segundos).
export const Campo: React.FC<{ t: number; p: Paleta; golpes: number[]; cx: number; cy: number }> = ({ t, p, golpes, cx, cy }) => {
  const puntos = Array.from({ length: 140 }, (_, i) => {
    const x = (rnd(i) * 1300 + t * (12 + rnd(i + 9) * 20)) % 1300 - 110;
    const y = rnd(i + 50) * 1920;
    return <circle key={i} cx={x} cy={y} r={2 + rnd(i + 3) * 5} fill={p.borde} opacity={0.15 + rnd(i + 7) * 0.35} />;
  });
  const ondas = golpes.filter((g) => t >= g && t < g + 1.4).map((g) => {
    const u = (t - g) / 1.4;
    return <circle key={g} cx={cx} cy={cy} r={120 + 700 * sale(u)} fill="none" stroke={p.acento} strokeWidth={14 * (1 - u)} opacity={1 - u} />;
  });
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
      {puntos}
      <circle cx={cx} cy={cy} r={220} fill={p.mar} opacity={0.5} />
      {ondas}
    </svg>
  );
};
