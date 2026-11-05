---
name: video
description: Hace un video vertical animado completo, de punta a punta, con el método del tutorial - analiza un enlace de referencia (opcional), propone 3 temas, guion con fuentes y 3 aperturas, voz (A tu voz clonada o B voz ya hecha), estilo en 3 cuadros, todas las escenas con revisor, música original, render a -14 LUFS e informe - deteniéndose a pedir aprobación en cada paso. Úsala cuando el usuario diga «hazme un video sobre…» o pegue un enlace para hacer uno parecido.
argument-hint: "<idea o enlace de referencia> [duración] [--sin-pausas]"
---

# Video de punta a punta

Habla **siempre en español**, de tú, sin tecnicismos innecesarios. Pedido: `$ARGUMENTS`.

`IA` = `python "${CLAUDE_PLUGIN_ROOT}/herramientas/ia.py"`. Reglas: `${CLAUDE_PLUGIN_ROOT}/REGLAS.md` (léelas una vez al empezar).

## Antes de empezar
1. La carpeta actual es la del video. Si no está vacía y no es de este plugin, propón una subcarpeta con nombre corto (p. ej. `hoyo-mexico/`) y trabaja ahí.
2. Corre `IA revisar`. Si falta algo, sigue `${CLAUDE_PLUGIN_ROOT}/skills/preparar/SKILL.md` y vuelve.
3. Crea `bitacora.md` y anota la hora de inicio y fin de cada paso (`Get-Date -Format "yyyy-MM-ddTHH:mm:ss"` en PowerShell o `date` en bash).

## Pasos (lee cada skill con Read al llegar; en cada ⏸ espera la respuesta del usuario)
| # | Paso del tutorial | Skill | Sale | ⏸ El usuario… |
|---|---|---|---|---|
| 1 | Analiza el enlace (solo si pasó enlace o video) | `${CLAUDE_PLUGIN_ROOT}/skills/analizar/SKILL.md` | `referencia/ANALISIS.md`, hoja de contacto | Lee el resumen de 10 líneas ⏸ |
| 2 | Elige el tema | `${CLAUDE_PLUGIN_ROOT}/skills/guion/SKILL.md` §1 | 3 temas con dato y fuente | Elige uno ⏸ |
| 3 | Guion y gancho | `…/skills/guion/SKILL.md` §2–3 | `guion.json`, `fuentes.md`, 3 aperturas | Aprueba guion y apertura ⏸ |
| 4 | La voz | `${CLAUDE_PLUGIN_ROOT}/skills/voz/SKILL.md` | `voz/narracion.wav`, `voz/tiempos.json`, `voz/calidad.json` | Elige A o B; si A, **confirma que es su voz** ⏸; escucha ⏸ |
| 5a | Estilo en 3 cuadros (agente `director-arte`) | `${CLAUDE_PLUGIN_ROOT}/skills/animar/SKILL.md` §1–2 | `arte/PROPUESTA.md`, `arte/STORYBOARD.md`, 3 PNG | Aprueba o corrige ⏸ |
| 5b | Todas las escenas + agente `revisor` | `…/skills/animar/SKILL.md` §3 | `revision/escenas/hoja.jpg` | Aprueba la hoja ⏸ |
| 6a | Música original | `…/skills/animar/SKILL.md` §4 | `audio/musica.wav`, `audio/efectos.wav` | Aprueba ⏸ |
| 6b | Render, revisor final e informe | `…/skills/animar/SKILL.md` §5–6 | `entrega/final.mp4`, `INFORME.md` | Lo ve en su celular ⏸ |

- Los 2 agentes del plugin son `animaciones-ia:director-arte` y `animaciones-ia:revisor` (herramienta Agent). Si no aparecen, lee su archivo en `${CLAUDE_PLUGIN_ROOT}/agents/` y haz tú su trabajo.
- **Una sola tarea pesada a la vez** en la tarjeta de video: no narres mientras renderizas.
- **Si un paso falla**: explica en una línea qué pasó, arréglalo una vez y, si sigue, dile al usuario qué hacer. No improvises herramientas nuevas.
- **Si algo se atora** (una descarga sin avanzar, un proceso que no escribe nada): las herramientas tienen tope de tiempo y reintentos y lo avisan. Si aun así algo lleva más de 5 min sin avanzar, detenlo, busca la causa, corrígelo y explícalo en dos líneas.

## Modo `--sin-pausas` (solo para pruebas)
No esperes respuestas: en cada ⏸ escribe en `bitacora.md` qué le habrías preguntado y qué elegiste, y sigue. Tema: el recomendado. Voz: si hay `mi_voz.wav` **y** el pedido dice que es del usuario, A; si no, **B (Piper)**. Correcciones de estilo: ninguna (pero el director de arte igual se autoexige y el revisor igual revisa).

## Al terminar
Dile: ruta de `entrega/final.mp4`, duración, LUFS, error de la voz, tiempo por paso (de `bitacora.md`) y 2–3 ideas para el siguiente. Recuérdale: verlo completo con audio en el celular antes de publicar, marcarlo como hecho con IA si la plataforma lo pide, y si usó un clon, que sea solo su voz.
