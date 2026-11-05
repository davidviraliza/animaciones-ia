// Curvas de movimiento: reciben un avance (0–1, se recorta) y devuelven otro. Cualquier función igual sirve como curva propia.
export type Curva = (x: number) => number;

export const cl = (x: number, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const suave: Curva = (x) => { x = cl(x); return x * x * x * (x * (6 * x - 15) + 10); }; // sin saltos de velocidad
export const sale: Curva = (x) => 1 - Math.pow(1 - cl(x), 3);
export const cae: Curva = (x) => { x = cl(x); return x * x; };
export const lineal: Curva = (x) => cl(x);
