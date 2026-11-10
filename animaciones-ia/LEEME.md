# Animaciones con IA · plugin gratuito para Claude Code

Hace videos verticales animados con el mismo método del tutorial: analiza un enlace, elige tema, escribe el guion con fuentes, narra con **tu voz clonada** o con una voz ya hecha, anima en Remotion con revisión cuadro por cuadro y le pone música original. Todo en tu PC, sin API ni créditos: solo tu plan de Claude.

**Necesitas:** Windows 10/11, Claude Pro o superior con Claude Code (app de Claude, pestaña **Code**), ~12 GB libres. Para clonar tu voz: tarjeta NVIDIA de 6 GB o más (sin ella usas la voz ya hecha).

## Instalar (1 minuto)
1. Abre la app de Claude, pestaña **Code**, y elige cualquier carpeta (por ejemplo `Documentos`).
2. Copia y pega este mensaje:
   ```
   Instala el plugin animaciones-ia: corre «claude plugin marketplace add davidviraliza/animaciones-ia» y luego «claude plugin install animaciones-ia@animaciones-con-ia». Avísame en español cuando termine.
   ```
3. Cuando Claude diga que terminó, cierra y vuelve a abrir la app.
4. Crea una carpeta para tu video (p. ej. `Documentos\videos\mi-video`), ábrela en la pestaña Code y escribe:
   `/animaciones-ia:preparar`
   Revisa tu PC e instala lo que falte. Te pide permiso antes de cada cosa.

¿Usas la terminal? `claude plugin marketplace add davidviraliza/animaciones-ia` y `claude plugin install animaciones-ia@animaciones-con-ia`.

## Usar
`/animaciones-ia:video <enlace de un video que te guste, o tu idea>`

Ejemplo: `/animaciones-ia:video https://www.tiktok.com/@cuenta/video/123 40 segundos`

Se detiene en cada paso para que apruebes: análisis → 3 temas → guion y 3 aperturas → voz → estilo en 3 cuadros → todas las escenas → música → video final con informe.

| Comando | Qué hace | Tarda |
|---|---|---|
| `/animaciones-ia:preparar` | Revisa e instala lo que falte | 10–30 min la 1.ª vez |
| `/animaciones-ia:video` | Todo, de punta a punta | 40–90 min el 1.º |
| `/animaciones-ia:analizar` | Estudia un enlace o video | 2–5 min |
| `/animaciones-ia:guion` | 3 temas y el guion con fuentes | 5–10 min |
| `/animaciones-ia:voz` | A: tu voz clonada · B: voz ya hecha | 3–10 min |
| `/animaciones-ia:animar` | Estilo, escenas, música y render | 20–40 min |

Agentes que trae: **director-arte** (propone el estilo en 3 cuadros y arma las escenas) y **revisor** (revisa cuadro por cuadro, volumen y voz antes de enseñarte nada).

## ¿Eres alumno del curso?

Con tu código personal (`FAB-XXXX-XXXX-XXXX`) este mismo plugin se actualiza a la **versión mejorada** (línea de 7 agentes, voz entrenada y más): escribe `/animaciones-ia:activar TU-CODIGO` y reinicia Claude. No necesitas GitHub.

## Si algo se atora
- **Una descarga no avanza:** espera; si en 60 s no baja nada, se reintenta sola. Si falla 5 veces, revisa tu internet y repite el mismo comando: sigue donde se quedó.
- **Un proceso no termina:** todo tiene tope de tiempo; se detiene solo y te dice dónde. Escríbele a Claude: «Se atoró. Detenlo, busca la causa, corrígelo y explícame en dos líneas».
- **«No se reconoce node/ffmpeg/python»:** cierra y vuelve a abrir Claude.
- **Te responde en inglés:** «Responde y describe todo en español, por favor».

## Bueno saber
- Claude no «ve» videos: ve cuadros fijos y lee la transcripción. Por eso revisa cuadro por cuadro y mide el audio; tú revisa el final con audio en tu celular.
- **Solo clona tu voz**, o la de alguien que te dio permiso por escrito.
- La referencia se baja **solo para estudiarla**: nunca resubas su video ni uses su material.
- Actualizar: pídele a Claude «corre `claude plugin marketplace update animaciones-con-ia`».
- Modelos y voces: `%LOCALAPPDATA%\animaciones-ia` (2–10 GB). Reglas: `REGLAS.md`. Licencias: `LICENCIAS.md`.
- Desinstalar: pídele a Claude «corre `claude plugin uninstall animaciones-ia@animaciones-con-ia`» y borra `%LOCALAPPDATA%\animaciones-ia`.
