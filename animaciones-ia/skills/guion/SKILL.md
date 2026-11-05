---
name: guion
description: Elige el tema y escribe el guion de un video vertical corto (25–60 s) - 3 temas con el mismo mecanismo viral de la referencia sin copiarla, cada dato con su fuente (lo dudoso se marca DUDA y no se usa) y 3 aperturas que compiten (frase, primera imagen y sonido de 0 a 3 s). Deja guion.json y fuentes.md listos para la voz. Úsala cuando el usuario quiera el tema, el guion o el texto de un video.
argument-hint: "<idea o tema> [duración en segundos]"
---

# Tema y guion

Habla **siempre en español**, de tú. Lee antes `${CLAUDE_PLUGIN_ROOT}/REGLAS.md` §1–2 y, si existe, `referencia/ANALISIS.md`.

Pedido: `$ARGUMENTS`. Si no dice duración: 30–40 s.

## 1. Elegir el tema (⏸)
- **Con referencia** (`referencia/ANALISIS.md`): propón **3 temas nuevos que funcionen con el MISMO mecanismo viral** sin copiar el tema ni las frases del original.
- **Sin referencia**: propón 3 enfoques distintos de la idea del usuario.

Para cada uno: el **gancho en una frase**, **por qué despierta curiosidad**, el **dato real que lo sostiene con su fuente** (búsqueda web: enciclopedia, institución, artículo serio) y **qué riesgo tiene** (dato discutido, tema muy visto, difícil de dibujar). Recomienda uno. ⏸ **Espera a que elija.** (Si quiere la misma idea del original: misma idea, con sus palabras, nunca copia textual.)

## 2. Escribir el guion
- **Datos:** cada cifra o hecho con una fuente que puedas citar, en `fuentes.md` (frase · dato · enlace · fecha de consulta). Si dos fuentes no coinciden, usa la más conservadora y di «unos» o «casi». Si algo **no se puede confirmar, márcalo DUDA en `fuentes.md` y no lo uses**. Nunca inventes.
- **Estructura:** la misma que el original si hay referencia (gancho → desarrollo con giro → cierre que invite a comentar); si no, gancho → datos → giro → remate.
- **Frases:** una frase = una escena (un cambio en pantalla), **máximo 14 palabras**, español de México natural, **números escritos como se dicen** («doce mil metros»). Total de palabras ≈ duración × 2.6.
- **Las 3 aperturas compiten:** escribe 3 aperturas distintas, cada una con **frase + primera imagen (cuadro 0) + sonido de 0 a 3 s**, de tipos distintos (A–E de REGLAS §1). Compáralas (¿abre una duda concreta?, ¿el cuadro 0 ya la muestra?, ¿el video la cumple?) y elige la mejor. **Prohibido empezar con «¿Sabías que…?»**, con «hola» o con intro.

Guarda `guion.json`:
```json
{
  "titulo": "Título corto",
  "duracion_objetivo": 35,
  "apertura": { "elegida": "A2", "frase": "…", "cuadro0": "…", "sonido": "…", "por_que": "…",
                "otras": [{ "id": "A1", "frase": "…", "cuadro0": "…", "sonido": "…" }, { "id": "A3", "…": "…" }] },
  "frases": [
    { "id": "p01", "bloque": "gancho", "texto": "Kola bajó doce kilómetros y no cruzó la corteza.", "ve": "contador 0 → 12 km, taladro", "fuentes": ["https://…"] },
    { "id": "p02", "bloque": "desarrollo", "texto": "…", "ve": "…", "fuentes": [] }
  ]
}
```
`id` = p01, p02… en orden. `bloque` = gancho, desarrollo, giro o cierre (la voz hace una pausa un poco más larga al cambiar de bloque). `texto` = exactamente lo que dirá la voz. `ve` = qué se ve (lo usa el director de arte).

## 3. Enséñalo (⏸)
Muestra: la tabla del guion (id · texto · qué se ve · fuente), la **duración estimada** (palabras ÷ 2.6), y las **3 aperturas con la elegida y por qué**. ⏸ **Espera su visto bueno.** Si pide cambios, edita `guion.json` y `fuentes.md`.

## Revisa antes de enseñarlo
- ¿La primera frase abre una duda que el video sí contesta? ¿Dura 2 s o menos?
- ¿Cada dato tiene enlace en `fuentes.md`? ¿Algún número suena demasiado bonito? Verifícalo otra vez.
- ¿Alguna frase copia textual a la referencia? Reescríbela.
