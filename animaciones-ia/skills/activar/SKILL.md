---
name: activar
description: Activa la versión mejorada de animaciones-ia (para alumnos del curso) con el código personal que te dio David (FAB-XXXX-XXXX-XXXX). Es el mismo plugin, actualizado a la versión de alumnos; no necesita cuenta de GitHub. Úsala cuando el usuario diga «activar», pegue un código FAB-… o pregunte cómo tener la versión de alumnos, la versión mejorada o de pago.
argument-hint: "FAB-XXXX-XXXX-XXXX"
---

# Activar la versión mejorada (alumnos del curso)

Habla en español, de tú, simple.

1. Si `$ARGUMENTS` no trae un código con forma `FAB-XXXX-XXXX-XXXX`, pídeselo: «Pégame tu código de alumno (te lo mandó David por Skool; empieza con FAB-)». No inventes ni adivines códigos.
2. Corre según su sistema (tiempo de espera de 10 min; baja ~20 MB en partes y avisa cada una):
   - **Windows:**
     ```
     powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/herramientas/fabrica.ps1" activar <CÓDIGO>
     ```
   - **Mac** (con chip Apple o Intel; no necesita instalar nada antes):
     ```
     bash "${CLAUDE_PLUGIN_ROOT}/herramientas/fabrica.sh" activar <CÓDIGO>
     ```
3. Según lo que diga:
   - **LISTO**: dile que cierre y vuelva a abrir Claude. Su animaciones-ia ya es la versión mejorada: los mismos comandos (`/animaciones-ia:video`, `/animaciones-ia:voz`…) ahora con la línea de 7 agentes y la voz entrenada. Primero `/animaciones-ia:preparar`. Para las versiones nuevas: `/animaciones-ia:actualizar`.
   - **FALTA_REGISTRAR**: corre tú los comandos `claude plugin …` que imprime (o pídele que los corra en la terminal), luego que reinicie Claude. En la app de escritorio, «Agregar marketplace» no acepta carpetas: tiene que ser por comando.
   - **NO SE PUDO**: léele el motivo tal cual (código desactivado, vencido, usado en demasiadas PCs, sin internet…). Si es del código, que le escriba a David por Skool. No reintentes más de una vez.
4. El código es personal: no lo repitas en otros lugares ni lo guardes en archivos del proyecto (la herramienta ya lo guarda en `%LOCALAPPDATA%\fabrica-ia\licencia.json`, o en Mac en `~/.local/share/fabrica-ia/licencia.json`).
5. La versión mejorada revisa una vez al día que la suscripción siga vigente. Si se termina, regresa sola a la versión gratis; sus videos, voces y reglas no se borran.
