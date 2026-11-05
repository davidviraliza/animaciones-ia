// Zona segura de 9:16 (REGLAS.md §3 del plugin): nada importante en y<400, y>1450 ni x>950. El gancho va en y≈850–1350.
import React from 'react';

export const ZONA = { yMin: 400, yMax: 1450, xMax: 950 };
export const GANCHO = { yMin: 850, yMax: 1350 };

export type Rect = { x: number; y: number; w: number; h: number };
export const cabe = (r: Rect) => r.y >= ZONA.yMin && r.y + r.h <= ZONA.yMax && r.x + r.w <= ZONA.xMax;

// Solo para revisar: se pone encima del video mientras se trabaja; no va en el render final.
export const GuiaZona: React.FC<{ gancho?: boolean }> = ({ gancho = false }) => {
  const velo = 'rgba(255,0,0,0.25)';
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: ZONA.yMin, background: velo }} />
      <div style={{ position: 'absolute', left: 0, top: ZONA.yMax, width: 1080, height: 1920 - ZONA.yMax, background: velo }} />
      <div style={{ position: 'absolute', left: ZONA.xMax, top: ZONA.yMin, width: 1080 - ZONA.xMax, height: ZONA.yMax - ZONA.yMin, background: velo }} />
      {gancho ? <div style={{ position: 'absolute', left: 0, top: GANCHO.yMin, width: ZONA.xMax, height: GANCHO.yMax - GANCHO.yMin, border: '2px dashed yellow', boxSizing: 'border-box' }} /> : null}
    </div>
  );
};
