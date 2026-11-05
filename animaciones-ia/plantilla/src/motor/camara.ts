// Cámara de un solo plano: da números (foco y escala); quien los aplica es el mundo. Las tomas se encadenan sin cortes.
import { Curva, lerp, suave } from './curvas';
import { EstiloCamara } from './estilo';

export type Plano = { fx: number; fy: number; s: number };
type Valores = { fx: number; s: number; [k: string]: number };

// Espacio en el que se interpola. a(): de un plano y su escala a valores interpolables (aquí se ponen topes);
// de(): de esos valores, con la escala y el foco ya con deriva, de vuelta a un plano.
export type Espacio<P extends Plano> = {
  a: (p: P, s: number) => Valores;
  de: (v: Valores, s: number, fx: number) => P;
};

const ESPACIO_SIMPLE: Espacio<Plano> = {
  a: (p, s) => ({ fx: p.fx, fy: p.fy, s }),
  de: (v, s, fx) => ({ fx, fy: v.fy, s }),
};

type Toma<P> = { t0: number; d: number; c: P; empuje: number };

export const crearCamara = <P extends Plano = Plano>(o: { planos?: Record<string, P>; curva?: Curva; espacio?: Espacio<P>; estilo?: EstiloCamara }) => {
  const planos = (o.planos ?? {}) as Record<string, P>;
  const curva = o.curva ?? suave;
  const espacio = o.espacio ?? (ESPACIO_SIMPLE as unknown as Espacio<P>);
  const { empuje: empujeBase = 0, escala = 0, lateral = 0, lateral2 = 0 } = o.estilo ?? {};
  const tomas: Toma<P>[] = [];
  let enOrden = false;

  // toma: en t0 empieza a ir, durante d segundos, al plano (nombre o literal); empuje = acercamiento lento por segundo
  const cam = (t0: number, d: number, plano: string | P, empuje = empujeBase) => {
    tomas.push({ t0, d, c: typeof plano === 'string' ? planos[plano] : plano, empuje });
    enOrden = false;
  };

  const camara = (t: number): P => {
    if (!enOrden) { tomas.sort((x, y) => x.t0 - y.t0); enOrden = true; }
    if (tomas.length === 0) throw new Error('la cámara no tiene tomas: falta cam(...)');
    const objetivo = (k: Toma<P>) => espacio.a(k.c, k.c.s * (1 + k.empuje * Math.max(0, t - k.t0)));
    let cur = objetivo(tomas[0]);
    for (let i = 1; i < tomas.length; i++) {
      const k = tomas[i];
      if (t < k.t0) break;
      const o2 = objetivo(k);
      const u = k.d > 0 ? curva((t - k.t0) / k.d) : 1;
      const mezcla: Valores = { ...cur };
      for (const c of Object.keys(o2)) mezcla[c] = lerp(cur[c], o2[c], u);
      cur = mezcla;
    }
    // deriva lenta: con estilo.camara la cámara nunca está del todo quieta
    const s = cur.s * (1 + escala * Math.sin(t * 0.47 + 0.6));
    const fx = cur.fx + lateral * Math.sin(t * 0.61) + lateral2 * Math.sin(t * 1.13 + 1);
    return espacio.de(cur, s, fx);
  };

  return { cam, camara };
};
