// Carga de la fuente: una vez por familia, y el render espera a que esté. El archivo vive en el --public-dir de cada composición.
import { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { EstiloFuente } from './estilo';

const pedidas = new Map<string, Promise<void>>();
const listas = new Set<string>();

export const fuenteLista = (f?: EstiloFuente) => !f || listas.has(f.familia);

export const cargarFuente = (f?: EstiloFuente): Promise<void> => {
  if (!f || typeof document === 'undefined') return Promise.resolve();
  const ya = pedidas.get(f.familia);
  if (ya) return ya;
  const h = delayRender(`fuente ${f.familia}`);
  const ff = new FontFace(f.familia, `url(${staticFile(f.archivo)}) format('truetype')`, { weight: f.peso ?? '100 900', stretch: f.anchura ?? '100%' });
  const p = ff.load()
    .then((x) => { document.fonts.add(x); })
    .catch((err) => { console.error(err); })
    .then(() => { listas.add(f.familia); continueRender(h); });
  pedidas.set(f.familia, p);
  return p;
};

// Para lo que mide con la fuente: vuelve a pintar cuando ya está, y el cuadro no se captura antes de ese repintado.
export const useFuente = (f?: EstiloFuente) => {
  const [lista, setLista] = useState(() => fuenteLista(f));
  const [espera] = useState(() => (lista ? null : delayRender(`medida con ${f?.familia}`)));
  useEffect(() => { if (!lista) cargarFuente(f).then(() => setLista(true)); }, [lista, f]);
  useEffect(() => { if (lista && espera !== null) continueRender(espera); }, [lista, espera]);
  return lista;
};
