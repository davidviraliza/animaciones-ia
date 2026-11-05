# Reglas de los videos (las aplica Claude en cada paso)

Salen de producir videos verticales de verdad y de lo que la gente sí ve. No son gustos: si una regla choca con lo que pides, Claude te lo dice antes de romperla.

## 1. Gancho (0–3 s)
- **El cuadro 0 nunca está vacío** ni negro: desde el primer cuadro ya se ve el tema (el globo, el objeto, el número).
- **La voz arranca en 0.0 s.** Nada de intro, logo ni «hola, bienvenidos».
- La primera frase dura **2 s o menos** y abre una duda concreta que el video sí contesta.
- Tipos de apertura (ninguno está probado como «el mejor»; la evidencia es débil o media, así que se elige por el tema):
  - **A. Escena en curso:** «Estás cavando un hoyo en tu patio…»
  - **B. Pregunta concreta:** «¿Dónde sales si cavas derecho desde México?»
  - **C. Creencia rota:** «No sales en China.» Solo si la sorpresa se cumple; el titular tramposo baja la confianza.
  - **D. Dato concreto:** «Kola bajó 12 km y no cruzó ni la corteza.»
  - **E. Mecanismo en marcha:** la imagen ya hace algo raro y la voz lo explica.
- Prohibido el gancho tramposo: lo que promete la apertura se cumple en el video.
- Prohibido abrir con «¿Sabías que…?», «hola» o una intro: está gastado y la gente se va.
- Las aperturas compiten: se escriben 3 (frase + cuadro 0 + sonido de 0 a 3 s) y se elige la mejor.

## 2. Guion
- **Frases-evento:** cada frase = un solo cambio en pantalla (gira el globo, cae un pin, corre un número). 6–14 palabras por frase.
- Ritmo de voz: ~2.6 palabras por segundo. Un video de 40 s lleva ~105 palabras; frases de máximo 14 palabras.
- **Cada dato con su fuente** (enlace) en `guion.json` y en `fuentes.md`. Si un dato no se pudo verificar, se marca **DUDA** y no se usa. Nada inventado, nada «aproximado» sin decirlo («unos», «casi»).
- Escribe los números como se dicen («doce mil metros»); en pantalla salen en cifra con `juntar` (ver la skill animar).
- Cierre corto: la respuesta o el remate. Sin «dale like».
- Si te basas en un video ajeno: se baja **solo para estudiarlo** (yt-dlp) y nunca se resube. Mismo mecanismo, estructura y ritmo, pero **tema o narración propios, nunca copia textual**, y nada de sus imágenes, su música ni su marca.

## 3. Pantalla
- **Una sola capa de texto**, palabra por palabra al ritmo de la voz. El mismo texto nunca sale dos veces a la vez.
- Sin cajas ni rectángulos detrás de las letras.
- Zona segura de 9:16 (1080×1920): nada importante arriba de y=400, abajo de y=1450 ni a la derecha de x=950 (ahí van los botones de la app).
- 1–2 palabras clave por frase, grandes y en color de acento; el resto, chicas.
- Nada genérico ni infantil: cada video tiene su paleta (cámbiala en `video/src/estilo.ts`) y tipografía fuerte.
- La cámara nunca está muerta: entrada rápida y frenado suave, deriva y una sacudida en cada golpe.
- Nivel «wow»: profundidad (capas al frente y al fondo, luz, partículas), textura (grano, sombras, degradados), protagonista grande que se reconoce al instante. Nada plano ni media pantalla vacía. Cada frase con un encuadre distinto: ninguna toma repetida.

## 4. Voz
- **Solo tu voz, o la de alguien que te dio permiso por escrito.** Nada de imitar a famosos, políticos ni creadores.
- Si la plataforma pide marcar contenido hecho con IA, márcalo.
- **A · tu voz clonada** (Chatterbox, NVIDIA 6 GB+): graba 20–30 s en un cuarto sin eco, hablando como en tus videos, y guárdala como `mi_voz.wav`. Antes de clonar, Claude te pide confirmar que es tu voz.
- **B · voz ya hecha** (Piper, sin tarjeta): español de México, para quien no tiene NVIDIA o no quiere usar su voz.
- Control de calidad: cada frase se transcribe y se regenera si no coincide con el guion (máximo 3 intentos); pausas de 0.10 a 0.25 s.

## 5. Música y sonido
- **Música original** con `ia.py musica` (se sintetiza nota por nota; la semilla queda guardada como prueba de autoría).
- No uses pistas «libres» famosas: aunque sean CC0, los sistemas automáticos de derechos las reclaman.
- Secciones que siguen el guion: entrada, desarrollo, tensión antes del giro y cierre; golpes en las palabras del storyboard.
- La música va **unos 18 dB debajo de la voz**; el volumen final queda en **−14 LUFS** con picos **bajo −1 dBTP** (lo mide `ia.py acabado`).

## 6. Antes de producir todo
- Primero se aprueba el estilo en **3 cuadros fijos** (inicio, mitad y final); luego todas las escenas en una hoja de contacto revisada por el agente revisor; luego la música; y hasta entonces el render.
- Después del render, el revisor vuelve a revisar: cuadros a tamaño completo, −14 LUFS y la transcripción contra el guion.
- Entrega: `entrega/final.mp4`, 1080×1920, 30 cuadros por segundo, e `INFORME.md`.
