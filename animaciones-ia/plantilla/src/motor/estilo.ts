// Estilo de un video: lo que cambia de uno a otro sin tocar la lógica. Aquí solo van los tipos y valores neutros; paleta, trazo y fuente son de cada video.
export type EstiloFuente = {
  familia: string;
  archivo: string; // relativo a --public-dir (staticFile)
  peso?: string; // rango de la fuente variable, para FontFace
  anchura?: string; // ídem, stretch
  variacion?: string; // font-variation-settings
  pesoCss?: number;
};

export type EstiloTexto = {
  color: string;
  colorPieza: string; // nombre de pieza o término clave
  anchoMax: number; // la palabra se reduce para caber aquí, centrada en x=540
  topeUna: number; // tamaño máximo: clave en una línea
  topeLiga: number; // palabra de enlace
  topeDos: number; // dos líneas
  yPie: number; // borde inferior de toda palabra
  altoLinea: number;
  altoLineaDos: number;
  bajoCentro?: number; // de centro de línea a línea base, en em. Sin este valor, se mide en el navegador
  escalaEntrada: number; // la palabra entra desde esta escala hasta 1
  cola?: { letras: string; fraccion: number; tope: number }; // letras que bajan de la línea base
  avances?: Record<string, number>; // avance por letra en em. Sin esta tabla, se mide en el navegador
  avanceOtro?: number;
};

export type EstiloCamara = { empuje?: number; escala?: number; lateral?: number; lateral2?: number };
export type EstiloTrazo = { grosor?: number; linea: string; desregistro?: { dx: number; dy: number } };

export type Estilo<P = Record<string, string>> = {
  fondo: string;
  paleta: P;
  fuente?: EstiloFuente;
  texto: EstiloTexto;
  camara?: EstiloCamara;
  trazo?: EstiloTrazo;
};

export const TEXTO_NEUTRO: Omit<EstiloTexto, 'color' | 'colorPieza'> = {
  anchoMax: 820, topeUna: 250, topeLiga: 170, topeDos: 142, yPie: 1446, altoLinea: 0.98, altoLineaDos: 0.84, escalaEntrada: 0.86,
};

type Entrada<P> = Omit<Estilo<P>, 'texto'> & { texto: Partial<EstiloTexto> & Pick<EstiloTexto, 'color' | 'colorPieza'> };
export const definirEstilo = <P,>(e: Entrada<P>): Estilo<P> => ({ ...e, texto: { ...TEXTO_NEUTRO, ...e.texto } });
