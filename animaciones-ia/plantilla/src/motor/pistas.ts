// Pistas: cada campo numérico del estado se mueve por segmentos encadenados; cada segmento parte de donde iba el anterior.
import { Curva, lerp, suave } from './curvas';

type Seg = { t0: number; d: number; v: number; c: Curva };
type Paso = { t: number; v: unknown };

export const crearPistas = <E extends object>(BASE: E) => {
  type Campo = keyof E & string;
  const pistas: Partial<Record<Campo, Seg[]>> = {};
  const escalones: Partial<Record<Campo, Paso[]>> = {};
  let enOrden = false;

  // en t0, durante d segundos, va al valor v con la curva c (d ≤ 0: salta)
  const a = (campo: Campo, t0: number, d: number, v: number, c: Curva = suave) => { (pistas[campo] ??= []).push({ t0, d, v, c }); enOrden = false; };
  // desde t, el campo vale v, sin transición; acepta cualquier tipo
  const escalon = <C extends Campo>(campo: C, t: number, v: E[C]) => { (escalones[campo] ??= []).push({ t, v }); enOrden = false; };

  const ordenar = () => {
    if (enOrden) return;
    Object.values<Seg[] | undefined>(pistas).forEach((p) => p?.sort((x, y) => x.t0 - y.t0));
    Object.values<Paso[] | undefined>(escalones).forEach((p) => p?.sort((x, y) => x.t - y.t));
    enOrden = true;
  };

  const valor = (campo: Campo, t: number) => {
    ordenar();
    let v = BASE[campo] as unknown as number;
    for (const s of pistas[campo] ?? []) {
      if (t < s.t0) break;
      v = s.d <= 0 ? s.v : lerp(v, s.v, s.c((t - s.t0) / s.d));
    }
    return v;
  };

  const estado = (t: number): E & { t: number } => {
    ordenar();
    const e = { ...BASE, t } as Record<string, unknown>;
    (Object.keys(pistas) as Campo[]).forEach((c) => { e[c] = valor(c, t); });
    (Object.keys(escalones) as Campo[]).forEach((c) => { for (const n of escalones[c] ?? []) if (t >= n.t) e[c] = n.v; });
    return e as E & { t: number };
  };

  return { a, escalon, valor, estado };
};
