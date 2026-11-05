// Cuadros fijos a tamaño completo con un solo empaquetado (más rápido que un «remotion still» por cuadro).
// Uso: node cuadros.mjs "0:C:/ruta/c0.png,135:C:/ruta/c1.png"   (cuadro:archivo, separados por coma)
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import path from 'node:path';

const pedidos = (process.argv[2] || '').split(',').filter(Boolean).map((x) => {
  const i = x.indexOf(':');
  return { cuadro: Number(x.slice(0, i)), archivo: x.slice(i + 1) };
});
if (!pedidos.length) {
  console.error('Uso: node cuadros.mjs "0:salida/c0.png,135:salida/c1.png"');
  process.exit(2);
}
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts') });
const composition = await selectComposition({ serveUrl, id: 'Video' });
for (const p of pedidos) {
  const frame = Math.min(Math.max(0, p.cuadro), composition.durationInFrames - 1);
  await renderStill({ composition, serveUrl, output: p.archivo, frame });
  console.log(`cuadro ${frame} → ${p.archivo}`);
}
