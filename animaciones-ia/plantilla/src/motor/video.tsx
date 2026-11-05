// Armado del video: fondo, Mundo(estado) y texto. Texto={null} lo quita; un componente propio lo sustituye.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Estilo } from './estilo';
import { cargarFuente } from './fuente';
import { GuiaFrase, Palabra, crearLetreros } from './texto';
import { TiemposVoz } from './voz';

type MundoFC<S> = React.ComponentType<{ e: S }>;

export const crearVideo = <S,>(o: {
  tiempos: TiemposVoz; estilo: Estilo<unknown>; Mundo: MundoFC<S>; estado: (t: number) => S;
  Texto?: React.ComponentType<{ t: number }> | null; guia?: GuiaFrase[]; soloNombre?: (i: number) => boolean; fps?: number;
}) => {
  const fps = o.fps ?? 30;
  cargarFuente(o.estilo.fuente);
  const Texto = o.Texto === undefined ? crearLetreros(o.tiempos, o.guia, { estilo: o.estilo, soloNombre: o.soloNombre, fps }).Texto : o.Texto;
  const { Mundo, estado } = o;
  // capa y lista son solo para revisar (remotion --props): sin ellas, el video de siempre. capa='texto' va sin fondo: el alfa del PNG es la máscara.
  const Video: React.FC<{ capa?: 'todo' | 'fondo' | 'texto'; lista?: number[] }> = ({ capa = 'todo', lista }) => {
    const c = useCurrentFrame();
    const t = (lista ? lista[c] : c) / fps;
    return (
      <AbsoluteFill style={capa === 'texto' ? undefined : { background: o.estilo.fondo }}>
        {capa === 'texto' ? null : <Mundo e={estado(t)} />}
        {Texto && capa !== 'fondo' ? <Texto t={t} /> : null}
      </AbsoluteFill>
    );
  };
  return { Video, cuadros: Math.ceil(o.tiempos.dur * fps) };
};

// Revisión: un cuadro por frase (frame i = frase i) con el estado acumulado al terminar esa frase, según la guía
// ({fin: campos, plano: nombre, palabras, pieza}), y la última palabra o el nombre. No es el video.
export type GuiaMuestra = GuiaFrase & { plano: string; fin: Record<string, unknown>; palabras: string[] };

export const crearMuestras = <S,>(o: {
  tiempos: TiemposVoz; guia: GuiaMuestra[]; base: S; planos: Record<string, unknown>; Mundo: MundoFC<S>; estilo: Estilo<unknown>;
}) => {
  cargarFuente(o.estilo.fuente);
  const estadoHasta = (i: number): S => {
    let e = { ...o.base } as S;
    for (let k = 0; k <= i; k++) e = { ...e, ...o.guia[k].fin, cam: o.planos[o.guia[k].plano] };
    return { ...e, t: o.tiempos.frases[i].fin };
  };
  const { Mundo } = o;
  const Muestras: React.FC = () => {
    const i = useCurrentFrame();
    const g = o.guia[i];
    const lineas = g.pieza ?? [g.palabras[g.palabras.length - 1].toUpperCase()];
    return (
      <AbsoluteFill style={{ background: o.estilo.fondo }}>
        <Mundo e={estadoHasta(i)} />
        <Palabra lineas={lineas} pieza={!!g.pieza} estilo={o.estilo} />
      </AbsoluteFill>
    );
  };
  return { estadoHasta, Muestras, cuadros: o.guia.length };
};
