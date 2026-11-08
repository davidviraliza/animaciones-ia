---
name: activar
description: Activa fabrica-ia, la versión completa para alumnos del curso, con el código personal que te dio David (FAB-XXXX-XXXX-XXXX). No necesita cuenta de GitHub. Úsala cuando el usuario diga «activar», pegue un código FAB-… o pregunte cómo instalar la versión de alumnos o fabrica-ia.
argument-hint: "FAB-XXXX-XXXX-XXXX"
---

# Activar fabrica-ia (alumnos del curso)

Habla en español, de tú, simple.

1. Si `$ARGUMENTS` no trae un código con forma `FAB-XXXX-XXXX-XXXX`, pídeselo: «Pégame tu código de alumno (te lo mandó David por Skool; empieza con FAB-)». No inventes ni adivines códigos.
2. Corre (tiempo de espera de 10 min; baja ~15 MB en partes y avisa cada una):
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/herramientas/fabrica.ps1" activar <CÓDIGO>
   ```
3. Según lo que diga:
   - **LISTO**: dile que cierre y vuelva a abrir Claude, y que luego escriba `/fabrica-ia:preparar` y después `/fabrica-ia:video <su idea>`. Para actualizar más adelante: `/fabrica-ia:actualizar`.
   - **FALTA_REGISTRAR**: escribe tú en Claude los dos comandos `/plugin …` que imprime (o pídele que los escriba), luego que reinicie Claude.
   - **NO SE PUDO**: léele el motivo tal cual (código desactivado, usado en demasiadas PCs, sin internet…). Si es del código, que le escriba a David por Skool. No reintentes más de una vez.
4. El código es personal: no lo repitas en otros lugares ni lo guardes en archivos del proyecto (la herramienta ya lo guarda en `%LOCALAPPDATA%\fabrica-ia\licencia.json`).
