// Tiempos de la voz: consulta de tiempos.json (o tiempos_estimados.json) por frase y palabra.
export type PalabraVoz = { w: string; s: number; e: number };
export type FraseVoz = { id: string; texto: string; ini: number; fin: number; palabras: PalabraVoz[] };
export type TiemposVoz = { dur: number; frases: FraseVoz[] };

// Sin acentos, sin signos, en minúsculas: «¿Cámara,» → «camara».
export const norm = (s: string) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\w]/g, '');

export const crearTiempos = <T extends TiemposVoz>(T: T, fps = 30) => {
  const FR: Record<string, FraseVoz> = Object.fromEntries(T.frases.map((f) => [f.id, f]));
  const I = (id: string) => FR[id].ini; // inicio de la frase
  const F = (id: string) => FR[id].fin; // fin de la frase
  const W = (id: string, p: string, n = 1) => { // inicio de la n-ésima palabra que empieza con p
    let k = 0;
    for (const x of FR[id].palabras) if (norm(x.w).startsWith(norm(p)) && ++k === n) return x.s;
    throw new Error(`no está «${p}» en ${id}`);
  };
  return { FR, I, F, W, cuadros: Math.ceil(T.dur * fps), fps };
};
