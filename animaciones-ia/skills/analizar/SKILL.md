---
name: analizar
description: Analiza un video de referencia (un enlace de TikTok, Instagram, YouTube o Facebook, o un mp4 que ya tengas) como analista de contenido viral - cortes de escena, transcripción palabra por palabra, gancho de 0 a 3 s, estructura, ritmo, estilo visual, audio y por qué se hizo viral - con hoja de contacto. Úsala cuando el usuario diga «analiza este video», «quiero uno como este» o pegue un enlace.
argument-hint: "<enlace o ruta del video>"
---

# Analizar un video de referencia

Habla **siempre en español**, de tú. Actúas como **analista de contenido viral y editor de video**. `IA` = `python "${CLAUDE_PLUGIN_ROOT}/herramientas/ia.py"`.

**Sé honesto desde el principio:** tú no ves el video en movimiento ni oyes el audio. Ves **cuadros fijos** que saca ffmpeg y lees la **transcripción con tiempos** de faster-whisper. El ritmo sale de medir cortes y palabras.

**Para qué se baja:** SOLO para estudiarlo. No se publica ni se reutiliza nada de su material (imágenes, música, frases, marca). Dilo así antes de bajarlo y pide permiso («¿Lo descargo para estudiarlo?»).

## Pasos
1. Referencia: `$ARGUMENTS` (enlace o archivo). Si no hay, pídela.
2. Corre (1–4 min; si es la primera vez y falta el entorno, manda a `/animaciones-ia:preparar`):
   ```
   IA analizar "<enlace o archivo>" referencia/analisis
   ```
   Con enlace, lo baja con yt-dlp a `referencia/referencia.mp4` (con progreso y reintentos) y guarda la ficha (cuenta, vistas, likes) en `referencia/ficha.json`. Si el enlace es privado o pide sesión, que lo baje él desde su teléfono y te pase el archivo.
3. Lee `referencia/analisis/ANALISIS_BASE.md` y **mira las imágenes**: todas las de `referencia/analisis/gancho/` (0 a 3 s) y las hojas de contacto `referencia/analisis/hojas/` (un cuadro por toma, en orden).
4. Escribe `referencia/ANALISIS.md`:
   - **Ficha:** duración, formato, cuenta, likes y vistas (de `ficha.json`; «—» si no hay).
   - **Tabla de escenas:** segundo de inicio y fin · qué se ve · qué dice la voz · texto en pantalla · movimiento de cámara.
   - **Ritmo:** palabras por segundo y duración promedio de cada toma.
   - **Gancho de 0 a 3 s**, separado en **frase, imagen y sonido**, y su tipo (A–E de `${CLAUDE_PLUGIN_ROOT}/REGLAS.md` §1).
   - **Estructura narrativa** paso a paso y **recursos de retención** (preguntas abiertas, cifras, giros, contadores).
   - **Estilo visual:** tipo de dibujo, paleta en hex (aproximada de los cuadros), tipografía, transiciones.
   - **Audio:** música, efectos y en qué palabras caen los golpes (de lo que se puede medir; lo que no, dilo).
   - **Cierre** o llamada a la acción.
   - **Por qué crees que se hizo viral**, separando **lo medido** de **tu opinión**.
   - **Datos que dice:** cada cifra, marcada «por verificar».
5. Enséñale la hoja de contacto (`referencia/analisis/hojas/hoja_01.jpg`) y un **resumen de 10 líneas**. ⏸ **No avances hasta que te diga.**
