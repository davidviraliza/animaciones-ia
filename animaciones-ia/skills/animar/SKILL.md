---
name: animar
description: Anima el video vertical 1080x1920 en Remotion con el método del tutorial - el agente director-arte propone el estilo en 3 cuadros fijos, el usuario aprueba, se construyen todas las escenas, el agente revisor revisa la hoja de contacto, música original con código (18 dB debajo de la voz), render a -14 LUFS y revisión final con transcripción. Úsala cuando ya hay guion.json y voz/tiempos.json y el usuario quiere el video.
argument-hint: "[nota de estilo opcional]"
---

# Animar, música, render y revisión

Habla **siempre en español**, de tú. `IA` = `python "${CLAUDE_PLUGIN_ROOT}/herramientas/ia.py"`. Necesitas `guion.json` y `voz/tiempos.json` aprobados. Reglas: `${CLAUDE_PLUGIN_ROOT}/REGLAS.md` §3, §5 y §6.

**Agentes del plugin** (herramienta Agent, `subagent_type`): `animaciones-ia:director-arte` y `animaciones-ia:revisor`. **Lo que responda el revisor lo guardas tú, tal cual, en `revision/<etapa>/REVISION.md`** (el usuario debe tenerlo en disco). En cada encargo dales: la carpeta del video, la ruta `IA` completa (con la ruta real del plugin, no la variable), la ruta de `REGLAS.md`, qué etapa hacen y la nota del usuario. Si los agentes no aparecen, lee su archivo (`${CLAUDE_PLUGIN_ROOT}/agents/<nombre>.md`) y haz tú ese trabajo siguiendo sus pasos.

**Una sola tarea pesada a la vez** en la tarjeta de video: no narres mientras renderizas.

## 1. Proyecto (solo la primera vez)
```
IA proyecto .
```
Copia la plantilla a `video/` e instala Remotion (1–3 min). La plantilla trae globo con mapa real, contador, palabra clave, subtítulo palabra por palabra y cámara viva; el director de arte la cambia y le agrega lo que el video pida.

## 2. Estilo en 3 cuadros (⏸)
Encarga a **`director-arte`, etapa A**: `arte/PROPUESTA.md` (paleta en hex, tipografía con carácter de Google Fonts, metáfora visual, cómo adapta la referencia sin copiarla), `arte/STORYBOARD.md` (una fila por frase: qué se ve, cámara, qué se mueve, palabra del golpe, texto en pantalla) y SOLO 3 cuadros fijos (inicio, mitad y final). **No se renderiza el video.**

Enséñale al usuario los 3 PNG y la propuesta en 5 líneas. ⏸ **Espera su aprobación o sus correcciones.** Si corrige (p. ej. «se ve plano y básico: nivel profesional, llena el cuadro, más profundidad y textura»), vuelve a encargar la etapa A con su nota tal cual y enséñale los 3 cuadros nuevos.

## 3. Todas las escenas + revisor (⏸)
1. Encarga a **`director-arte`, etapa B**: todas las escenas ancladas a `voz/tiempos.json`, mismo nivel de acabado en todas, sin tomas repetidas, con su hoja de contacto propia. Sin render.
2. Encarga al **`revisor`**, etapa `escenas`: hoja de contacto (un cuadro por frase), cuadros dudosos a tamaño completo, veredicto con motivo exacto.
3. Si **REGRESA**: pasa su lista tal cual a `director-arte` (etapa B, corrección) y luego otra vez al revisor. **Máximo 1 regreso**; si sigue fallando, enséñale al usuario lo que falla y pregúntale.
4. Enséñale al usuario `revision/escenas/hoja.jpg` y la lista de lo corregido. ⏸ **Todavía no renderices: espera su visto bueno.** Si pide cambiar escenas (p. ej. «en la 2, 4 y 5 se repite la toma»), encárgalo al director de arte y enséñale solo esos cuadros corregidos.

## 4. Música original (⏸)
```
IA musica --voz voz/narracion.wav --tiempos voz/tiempos.json --giro <id del giro> --golpes <id:palabra,…> --salida audio/musica.wav
```
- Se compone con código (síntesis en Python con numpy, sin samples ni canciones con derechos), con **entrada, desarrollo, tensión antes del giro y cierre**. El giro y los golpes salen del `STORYBOARD.md` (columna de golpes) y del `bloque` del guion. Los golpes quedan en `audio/efectos.wav`.
- Tarda segundos. Si pasa de 2 min, algo está mal: tiene tope y se detiene solo.
- Explícale en **5 líneas** qué hiciste (semilla, tono, secciones, golpes; la semilla en `audio/musica.json` es su prueba de autoría). Si no le gusta, otra semilla: `--semilla 12345`. ⏸ **Espera su visto bueno antes del render.**

## 5. Render y acabado
```
cd video
npx remotion render src/index.ts Video salida/render.mp4 --codec h264 --crf 18 --color-space=bt709 --muted
cd ..
IA acabado --video video/salida/render.mp4 --voz voz/narracion.wav --musica audio/musica.wav --efectos audio/efectos.wav --salida entrega/final.mp4
```
- 30–40 s de video tardan ~2–8 min según la PC. Corre con tiempo de espera largo.
- `acabado` pone la música **18 dB debajo de la voz**, deja **−14 LUFS** y **picos bajo −1 dBTP**, y lo mide. Debe decir `OK`.

## 6. Revisión final e informe (⏸)
1. Encarga al **`revisor`**, etapa `final`: hoja de contacto del mp4, cuadros a tamaño completo, y `IA medir` (volumen, picos, cuadro 0, duración, **transcripción del video contra el guion**). Si REGRESA, corrige (lo visual con `director-arte`; el audio tú) y vuelve a pasar por el revisor una vez.
2. Escribe `INFORME.md`: resultado de cada prueba (tabla de `revision/final/MEDICION.md`), cuánto tardó cada paso (copiado de las horas de `bitacora.md`, sin estimar) y qué conviene mejorar para el siguiente video.
3. Dile: ruta de `entrega/final.mp4`, duración, LUFS, y que lo vea **completo con audio en su celular** antes de publicarlo (tú no oyes ni ves el movimiento: solo mides). Ábrelo si lo pide. ⏸
