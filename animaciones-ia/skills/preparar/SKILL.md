---
name: preparar
description: Revisa la PC del usuario (Windows) e instala lo que falte para hacer videos animados con IA - Node LTS, ffmpeg, Python 3.11, transcripción, voz B (Piper, sin tarjeta de video) y, si tiene NVIDIA de 6 GB o más y lo quiere, voz A (Chatterbox, su voz clonada). Úsala cuando el usuario quiera preparar su PC, cuando algo de Animaciones con IA diga que falta una herramienta o antes del primer video.
argument-hint: "[--clon si quieres clonar tu voz]"
---

# Preparar la PC

Habla **siempre en español**, de tú, en lenguaje simple. Antes de cada instalación di **qué es, para qué sirve y cuánto pesa**, y pide permiso («¿Lo instalo?»). No pidas permisos de administrador si no hacen falta.

`IA` = `python "${CLAUDE_PLUGIN_ROOT}/herramientas/ia.py"`.

## 1. Ver qué hay (no instala nada)
```
IA revisar
```
Si `python` no existe o abre la Tienda de Microsoft, corre antes los comandos de la tabla del paso 2 para Python. Explícale la tabla al usuario en 3–5 líneas.

## 2. Instalar lo que falte (con winget, una cosa a la vez)
| Falta | Para qué | Comando | Administrador |
|---|---|---|---|
| Node.js LTS (~30 MB) | Corre Remotion, el programa que dibuja el video | `winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements` | Sí, **una vez** (Windows pregunta «¿Permitir cambios?») |
| ffmpeg (~100 MB) | Corta, mezcla y mide audio y video | `winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements` | No |
| Python 3.11 (~30 MB) | Corre la voz y la transcripción | `winget install -e --id Python.Python.3.11 --scope user --accept-source-agreements --accept-package-agreements` | No |

- Sin `winget`: que abra la Microsoft Store, busque «Instalador de aplicación» y lo actualice.
- **Windows no ve los programas nuevos hasta reiniciar.** Dile que cierre y vuelva a abrir Claude y escriba otra vez `/animaciones-ia:preparar`. Es normal.

## 3. Entorno del plugin (transcripción, descargas y voces)
Pregunta primero: **¿quieres narrar con tu propia voz clonada?** Solo se puede con tarjeta NVIDIA de 6 GB o más (lo dice `IA revisar`). Si no tiene o no quiere, usará la **voz B** (ya hecha, en español de México, sin tarjeta).

- Solo voz B (cualquier PC): `IA instalar` — ~2 GB de descarga, 5–10 min.
- Voz A y B (NVIDIA 6 GB+): `IA instalar --clon` — ~7 GB de descarga, 15–30 min.

Córrelo con tiempo de espera largo (hasta 60 min). **Verás el avance**: cada paso dice «n/total», cada descarga dice cuántos MB lleva cada 10 s y, si una se queda quieta 60 s, la corta y reintenta sola reanudando donde iba. Si pasa medio minuto sin salida, aparece «… sigue trabajando». Ningún comando se queda colgado: tiene un tope y se detiene solo avisando.

Todo queda en `%LOCALAPPDATA%\animaciones-ia` (o en la carpeta de la variable `ANIMACIONES_IA_DATOS`), no en la carpeta del video.

## 4. Qué decir al final
- Qué quedó instalado y qué no (corre `IA revisar` otra vez).
- Qué voz puede usar: **A** (su voz clonada con Chatterbox, ~2–5 s por frase en una tarjeta de 6 GB) o **B** (Piper, voz ya hecha de español de México: rápida, sin tarjeta, suena menos natural).
- Siguiente paso: `/animaciones-ia:video <tu idea o el enlace de un video que te guste>`.

## Si algo se atora
- Una descarga dice «se detuvo… reintento»: es normal, sigue sola. Si falla 5 veces: revisa el internet y corre **el mismo comando** otra vez (reanuda, no empieza de cero).
- «ALTO: llegó a su tope»: algo se atoró. Lee las últimas líneas, explica en dos líneas qué pasó y vuelve a correrlo una vez.
- «No se reconoce node/ffmpeg/python» justo después de instalar: falta reiniciar Claude.
- El antivirus bloquea `esbuild` o el Chrome de Remotion: dile qué archivo y que lo permita; no lo desactives tú.
