// Estilo del video: paleta y tipografía. Se elige con "paleta" en escenas.json; cambia los colores aquí para darle a tu video su propia esencia.
import { definirEstilo } from './motor';

export type Paleta = {
  fondo: string; // lo que no es planeta
  mar: string; // océano del globo
  tierra: string; // continentes
  borde: string; // costa y retícula
  texto: string; // palabras normales
  acento: string; // palabras clave, pines, contador
  brillo: string; // halo del globo
};

export const PALETAS: Record<string, Paleta> = {
  noche: { fondo: '#0B0B1E', mar: '#14306B', tierra: '#3FB58A', borde: '#7FE0C0', texto: '#FFFFFF', acento: '#FFC21A', brillo: '#3A7BFF' },
  lava: { fondo: '#150926', mar: '#21103A', tierra: '#8C63D6', borde: '#CBA6FF', texto: '#FFFFFF', acento: '#FF7A1A', brillo: '#D32A5C' },
  papel: { fondo: '#F2E8D5', mar: '#9BC4D9', tierra: '#D9A35F', borde: '#5B3A1E', texto: '#1E140A', acento: '#D3122E', brillo: '#FFFFFF' },
};

export const crearEstilo = (nombre: string) => {
  const p = PALETAS[nombre] ?? PALETAS.noche;
  return {
    paleta: p,
    estilo: definirEstilo({
      fondo: p.fondo,
      paleta: p,
      // Big Shoulders Display: licencia SIL OFL 1.1 (public/fuentes/bigshouldersdisplay_OFL.txt). Si cambias de fuente, usa una con licencia libre.
      fuente: { familia: 'BigShouldersDisplay', archivo: 'fuentes/BigShouldersDisplay.ttf', peso: '100 900', pesoCss: 900 },
      texto: { color: p.texto, colorPieza: p.acento, anchoMax: 840, topeUna: 250, topeLiga: 170, topeDos: 170, yPie: 1446, altoLineaDos: 0.98 },
    }),
  };
};
