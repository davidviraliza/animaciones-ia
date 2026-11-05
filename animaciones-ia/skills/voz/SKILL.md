---
name: voz
description: Narra guion.json en la PC del usuario, gratis y con licencia comercial - opción A su propia voz clonada con Chatterbox (MIT, grabación mi_voz.wav de 20–30 s, NVIDIA de 6 GB o más) u opción B una voz ya hecha en español de México sin tarjeta de video (Piper). Control de calidad frase por frase con faster-whisper, hasta 3 intentos, pausas de 0.10 a 0.25 s y tiempos de cada palabra. Úsala para la voz, la narración o para clonar «mi voz».
argument-hint: "[A | B]"
---

# Voz

Habla **siempre en español**, de tú. `IA` = `python "${CLAUDE_PLUGIN_ROOT}/herramientas/ia.py"`. Necesitas `guion.json` aprobado.

## 1. Elegir el camino
Pregunta (si no lo dijo):
- **A · Tu voz clonada** — necesitas tarjeta NVIDIA de 6 GB o más y una grabación tuya de **20–30 s** hablando normal, en un cuarto sin eco, guardada en la carpeta como **`mi_voz.wav`** (la grabadora de Windows o el celular sirven; cualquier formato).
- **B · Una voz ya hecha** — sin tarjeta de video, en español de México. Suena menos natural, pero funciona en cualquier PC.

**Diagnostica el equipo** con `IA revisar` (tarjeta, memoria de video, espacio). Si eligió A y su equipo no alcanza, díselo, recomienda B y **para** hasta que responda.

**Por qué estos modelos** (dilo en 2–3 líneas): A = **Chatterbox Multilingual** de Resemble AI, licencia **MIT** (uso comercial permitido), habla español y clona con una muestra corta; otros modelos famosos de clonación no permiten uso comercial. B = **Piper** con la voz `es_MX-claude-high`, gratis y sin tarjeta (licencias en `${CLAUDE_PLUGIN_ROOT}/LICENCIAS.md`).

## 2A. Opción A: confirma que la voz es suya (⏸ obligatorio)
**Solo se clona tu propia voz, o la de alguien que te dio permiso por escrito.** Nada de famosos, políticos ni creadores. Pregunta textualmente: «¿Confirmas que `mi_voz.wav` es tu voz y me autorizas a instalar lo necesario para clonarla?» ⏸ **No sigas sin un sí explícito.** Si dice que es de otra persona sin permiso: no la clones y ofrece la opción B.

Con el sí:
1. Si `IA revisar` dice que Chatterbox no está: `IA instalar --clon` (15–30 min; avisa que verá el avance y que, si una descarga se queda quieta, se reintenta sola).
2. Registra la muestra (revisa duración y saturación):
   ```
   IA voz revisar-muestra --muestra mi_voz.wav --es-mi-voz
   ```
   (con permiso de otra persona: `--tengo-permiso "Nombre, cómo y cuándo lo dio"` en vez de `--es-mi-voz`).
3. Narra:
   ```
   IA voz narrar --guion guion.json --motor chatterbox --voz voces/mi_voz.json
   ```

## 2B. Opción B: voz ya hecha
```
IA voz narrar --guion guion.json --motor piper
```

## 3. Control de calidad (lo hace la herramienta; tú lo explicas)
- Narra **frase por frase** con estilo natural y conversacional.
- **Transcribe cada frase con faster-whisper**; si alguna palabra no coincide con el guion, **regenera esa frase (máximo 3 intentos)** y se queda la mejor. Cada intento se imprime con sus errores.
- Une las frases con **pausas de 0.10 a 0.25 s** (más larga tras pregunta o cambio de bloque) y guarda los **tiempos de cada palabra** en `voz/tiempos.json`.
- Sale: `voz/narracion.wav`, `voz/tiempos.json` y `voz/calidad.json`.
- La primera vez baja los modelos (con progreso). Corre con tiempo de espera largo (hasta 60 min).

## 4. Reporta (⏸)
- **Duración final** y **porcentaje de error por palabra** (de `voz/calidad.json`), y cuántas frases necesitaron más intentos.
- Si dice **REVISA**: esas frases siguen distintas tras 3 intentos. Muéstralas (guion vs. lo que se oyó). Si es un nombre propio o un número que whisper escribe distinto, suele estar bien; si no, cambia una palabra de la frase o rehazla con `--rehacer p03`.
- Si la duración no cuadra con lo planeado, ofrece opciones; si dice «déjala así», se deja: **la voz natural vale más que el ritmo exacto**.
- Pide que escuche `voz/narracion.wav`. ⏸ **Espera su visto bueno** antes de animar.
