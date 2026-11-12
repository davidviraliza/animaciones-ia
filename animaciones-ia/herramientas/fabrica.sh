#!/bin/bash
# animaciones-ia para Mac (y Linux): lo mismo que fabrica.ps1 en Windows. Pasa de la versión gratis a la mejorada (alumnos)
# con tu código personal, la actualiza y revisa que tu suscripción siga vigente. Si ya no lo está, regresa sola a la gratis.
#   bash fabrica.sh activar FAB-XXXX-XXXX-XXXX
#   bash fabrica.sh actualizar | estado | revisar | volver-gratis
# No necesita GitHub ni programas extra: usa curl, unzip y el JavaScript que ya trae macOS (osascript).
ACCION="${1:-estado}"
CODIGO="${2:-}"

# En Windows esto lo hace fabrica.ps1: si llegamos aquí desde Windows, no hacemos nada.
[ -z "$FABRICA_IA_PRUEBA_SH" ] && case "$(uname -s 2>/dev/null)" in MINGW*|MSYS*|CYGWIN*|Windows*) exit 0 ;; esac

SERVIDOR='https://script.google.com/macros/s/AKfycbwNhtbg-iKdQPmxslWXqxeHjZdDhSoaRdlrPHrvzUaQw_RyT0niQTCYzrogKQ8j6uV_/exec'
MK='animaciones-con-ia'
PLUGIN='animaciones-ia@animaciones-con-ia'
REPO_GRATIS='davidviraliza/animaciones-ia'
REVISAR_CADA_HORAS=24
DIAS_SIN_INTERNET=10

DATOS="${FABRICA_IA_DATOS:-$HOME/.local/share/fabrica-ia}"   # la misma carpeta que usan las herramientas de Python
mkdir -p "$DATOS"
LICENCIA="$DATOS/licencia.json"
INSTALADO="$DATOS/plugin_instalado.json"
DESTINO="$DATOS/plugin"
ANTERIOR="$DATOS/plugin_anterior"
TMPD="$(mktemp -d "${TMPDIR:-/tmp}/fabrica-ia.XXXXXX")"
trap 'rm -rf "$TMPD"' EXIT

ahora() { date '+%Y-%m-%dT%H:%M:%S'; }
salir() { [ -n "$1" ] && printf '%s\n' "$1"; exit "$2"; }

# ---------- JSON (osascript en Mac; python3 en Linux) ----------
# j <op> <args…>:  get ARCH CLAVE · set ARCH CLAVE VALOR [CLAVE VALOR…] · horas ISO · plugver ARCH PLUGIN · mk ARCH NOMBRE · b64 ARCH CLAVE SALIDA
JS='function run(a){ObjC.import("Foundation");
 var leer=function(p){var s=$.NSString.stringWithContentsOfFileEncodingError(p,$.NSUTF8StringEncoding,null);return s.isNil()?"":s.js;};
 var json=function(p){try{return JSON.parse(leer(p));}catch(e){return null;}};
 var op=a[0];
 if(op=="get"){var o=json(a[1]);var v=o?o[a[2]]:undefined;return (v===undefined||v===null)?"":String(v);}
 if(op=="set"){var o=json(a[1])||{};for(var i=2;i+1<a.length;i+=2)o[a[i]]=a[i+1];
   $.NSString.alloc.initWithUTF8String(JSON.stringify(o,null,2)).writeToFileAtomicallyEncodingError(a[1],true,$.NSUTF8StringEncoding,null);return "";}
 if(op=="horas"){var t=new Date(a[1]).getTime();return isNaN(t)?"9999":String(Math.floor((Date.now()-t)/36e5));}
 if(op=="plugver"){var t=leer(a[1]),i=t.indexOf("[");if(i<0)return "";try{var l=JSON.parse(t.slice(i));}catch(e){return "";}
   for(var k=0;k<l.length;k++){var p=l[k];if(p.id==a[2]||(p.name+"@"+p.marketplace)==a[2])return String(p.version||"");}return "";}
 if(op=="mk"){var t=leer(a[1]),i=t.indexOf("[");if(i<0)return "";try{var l=JSON.parse(t.slice(i));}catch(e){return "";}
   for(var k=0;k<l.length;k++){if(l[k].name==a[2])return "si|"+(l[k].repo||"")+"|"+(l[k].path||"");}return "";}
 if(op=="b64"){var o=json(a[1]);if(!o||!o[a[2]])return "no";
   var d=$.NSData.alloc.initWithBase64EncodedStringOptions(o[a[2]],1);if(d.isNil())return "no";return d.writeToFileAtomically(a[3],true)?"si":"no";}
 return "";}'
PY='import sys,json,datetime,base64
a=sys.argv[1:];op=a[0]
def leer(p):
  try: return open(p,encoding="utf-8").read()
  except Exception: return ""
def js(p):
  try: return json.loads(leer(p))
  except Exception: return None
def lista(p):
  t=leer(p);i=t.find("[")
  try: return json.loads(t[i:]) if i>=0 else []
  except Exception: return []
if op=="get":
  o=js(a[1]) or {};v=o.get(a[2]);print("" if v is None else ("true" if v else "false") if isinstance(v,bool) else v)
elif op=="set":
  o=js(a[1]) or {}
  for i in range(2,len(a)-1,2): o[a[i]]=a[i+1]
  open(a[1],"w",encoding="utf-8").write(json.dumps(o,ensure_ascii=False,indent=2))
elif op=="horas":
  try: print(int((datetime.datetime.now()-datetime.datetime.fromisoformat(a[1])).total_seconds()//3600))
  except Exception: print(9999)
elif op=="plugver":
  print(next((str(p.get("version","")) for p in lista(a[1]) if p.get("id")==a[2] or "%s@%s"%(p.get("name"),p.get("marketplace"))==a[2]),""))
elif op=="mk":
  print(next(("si|%s|%s"%(m.get("repo") or "",m.get("path") or "") for m in lista(a[1]) if m.get("name")==a[2]),""))
elif op=="b64":
  o=js(a[1]) or {}
  try: open(a[3],"wb").write(base64.b64decode(o[a[2]]));print("si")
  except Exception: print("no")'
j() {
    if command -v osascript >/dev/null 2>&1; then osascript -l JavaScript -e "$JS" "$@" 2>/dev/null
    else PYTHONIOENCODING=utf-8 python3 -c "$PY" "$@" 2>/dev/null; fi
}

# Sin lector de JSON no se puede leer la licencia: nunca se toma eso como «sin código» (no se regresa a la gratis por eso)
if ! command -v osascript >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    [ "$ACCION" = revisar ] && exit 0
    salir 'ERROR: falta python3 para leer las respuestas del servidor. Instálalo y vuelve a intentar.' 4
fi

# Identificador de esta computadora (no es personal: un resumen de nombre de equipo + usuario)
NOMBRE_EQUIPO="$(scutil --get ComputerName 2>/dev/null || hostname 2>/dev/null)"
MAQUINA="$(printf '%s|%s' "$NOMBRE_EQUIPO" "${USER:-$(id -un)}" | shasum -a 256 2>/dev/null | cut -c1-16)"
[ -n "$MAQUINA" ] || MAQUINA="$(printf '%s|%s' "$NOMBRE_EQUIPO" "${USER:-$(id -un)}" | sha256sum | cut -c1-16)"

# pedir SALIDA INTENTOS ESPERA clave=valor…  → deja la respuesta del servidor en SALIDA
pedir() {
    local sal="$1" intentos="$2" espera="$3"; shift 3
    local args=() kv
    for kv in "$@"; do args+=(--data-urlencode "$kv"); done
    local i=1
    while [ "$i" -le "$intentos" ]; do
        if curl -sSL -G --max-time "$espera" "${args[@]}" "$SERVIDOR" -o "$sal" 2>"$TMPD/curl_err" && [ -s "$sal" ]; then return 0; fi
        [ "$i" -lt "$intentos" ] && sleep $((5 * i))
        i=$((i + 1))
    done
    return 1
}

# ---------- Claude Code (comando claude) ----------
# Quien solo usa la app de escritorio no tiene «claude» en el PATH: la app trae el suyo.
buscar_claude() {
    local c p
    c="$(command -v claude 2>/dev/null)"; [ -n "$c" ] && { echo "$c"; return; }
    if [ -n "$CLAUDE_PID" ]; then                               # el Claude que nos está corriendo ahora mismo
        p="$(ps -o comm= -p "$CLAUDE_PID" 2>/dev/null | head -1)"
        case "$(basename "$p" 2>/dev/null)" in claude) [ -x "$p" ] && { echo "$p"; return; } ;; esac
    fi
    local raiz
    for raiz in "$HOME/Library/Application Support/Claude" "/Applications/Claude.app/Contents" "$HOME/Applications/Claude.app/Contents" \
                "$HOME/.local/bin" "$HOME/.claude/local" "/opt/homebrew/bin" "/usr/local/bin"; do
        [ -d "$raiz" ] || continue
        find "$raiz" -maxdepth 7 -type f -name claude -perm -u+x 2>/dev/null
    done | while IFS= read -r f; do printf '%s\t%s\n' "$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo 0)" "$f"; done \
      | sort -rn | head -1 | cut -f2-
}
CLAUDE_EXE=""
[ -z "$FABRICA_IA_SIN_REGISTRAR" ] && CLAUDE_EXE="$(buscar_claude)"

cli() { "$CLAUDE_EXE" "$@" >"$TMPD/cli.txt" 2>&1; }       # deja la salida en cli.txt; devuelve el código de claude
version_en_claude() { cli plugin list --json; j plugver "$TMPD/cli.txt" "$PLUGIN"; }

usar_fuente() {   # usar_fuente FUENTE ES_CARPETA(0/1): cambia de dónde sale animaciones-ia y lo deja instalado
    local fuente="$1" carpeta="$2" act repo ruta mismo=0
    cli plugin marketplace list --json; cp "$TMPD/cli.txt" "$TMPD/mks.txt"
    if [ -n "$(j mk "$TMPD/mks.txt" fabrica-ia)" ]; then           # el plugin aparte de antes: ya no se usa
        cli plugin uninstall fabrica-ia@fabrica-ia; cli plugin marketplace remove fabrica-ia
    fi
    act="$(j mk "$TMPD/mks.txt" "$MK")"
    if [ -n "$act" ]; then
        repo="$(echo "$act" | cut -d'|' -f2)"; ruta="$(echo "$act" | cut -d'|' -f3-)"
        if [ "$carpeta" = 0 ] && [ "$repo" = "$fuente" ]; then mismo=1; fi
        if [ "$carpeta" = 1 ] && [ -n "$ruta" ] && [ "$(cd "$ruta" 2>/dev/null && pwd -P)" = "$(cd "$fuente" && pwd -P)" ]; then mismo=1; fi
    fi
    if [ "$mismo" = 1 ]; then cli plugin marketplace update "$MK"
    else
        [ -n "$act" ] && cli plugin marketplace remove "$MK"
        if ! cli plugin marketplace add "$fuente"; then echo "Claude no aceptó la fuente del plugin: $(cat "$TMPD/cli.txt")" >&2; return 1; fi
    fi
    if ! cli plugin install "$PLUGIN" || grep -qi already "$TMPD/cli.txt"; then cli plugin update "$PLUGIN"; fi
    cli plugin enable "$PLUGIN"
    version_en_claude
}

volver_gratis() {   # quita la versión mejorada de esta computadora y deja la gratis; videos, voces y reglas no se tocan
    rm -rf "$DESTINO" "$ANTERIOR" "$INSTALADO"
    [ -f "$LICENCIA" ] && j set "$LICENCIA" terminado "$(ahora)" motivo "$1"
    if [ -n "$CLAUDE_EXE" ]; then
        local v; v="$(usar_fuente "$REPO_GRATIS" 0 2>/dev/null)"
        [ -n "$v" ] && { echo "VERSION_GRATIS: se regresó a animaciones-ia $v (gratis)."; return; }
        echo "VERSION_GRATIS: se quitó la versión mejorada. Si animaciones-ia no aparece, en Claude escribe  /plugin marketplace add $REPO_GRATIS  y  /plugin install $PLUGIN"
        return
    fi
    echo 'VERSION_GRATIS: se quitó la versión mejorada de esta computadora.'
}

case "$ACCION" in activar|actualizar|estado|revisar|volver-gratis) ;; *) salir "ERROR: acción desconocida «$ACCION». Usa: activar CÓDIGO, actualizar, estado, revisar o volver-gratis." 2 ;; esac

# ---------- estado ----------
if [ "$ACCION" = estado ]; then
    [ -f "$INSTALADO" ] || salir 'animaciones-ia versión mejorada: no está activada en esta computadora (tienes la gratis). Usa: activar TU-CODIGO' 1
    vence="$(j get "$LICENCIA" vence)"; ult="$(j get "$LICENCIA" ultima_ok)"
    t="animaciones-ia $(j get "$INSTALADO" version) (versión mejorada) instalada el $(j get "$INSTALADO" fecha)."
    [ -n "$vence" ] && t="$t Suscripción vigente hasta el $vence."
    [ -n "$ult" ] && t="$t Última revisión: $ult."
    salir "$t" 0
fi

# ---------- volver-gratis (a mano) ----------
[ "$ACCION" = volver-gratis ] && salir "$(volver_gratis 'a petición del usuario')" 0

# ---------- revisar (al abrir Claude; lo corre el hook de la versión mejorada) ----------
if [ "$ACCION" = revisar ]; then
    AVISO='[animaciones-ia] '
    cod="$(j get "$LICENCIA" codigo)"
    if [ -z "$cod" ]; then
        r="$(volver_gratis 'sin código en esta computadora')"
        salir "${AVISO}Esta computadora no tiene código de alumno, así que la versión mejorada no puede usarse aquí. $r Dile al usuario, en español, que cierre y vuelva a abrir Claude, y que si es alumno use /animaciones-ia:activar con su código. No uses los comandos de la versión mejorada en esta sesión." 0
    fi
    ult="$(j get "$LICENCIA" ultima_ok)"; horas=9999
    [ -n "$ult" ] && horas="$(j horas "$ult")"; horas="${horas:-9999}"
    [ "$horas" -lt "$REVISAR_CADA_HORAS" ] 2>/dev/null && salir '' 0
    if ! pedir "$TMPD/r.json" 1 20 accion=estado "codigo=$cod" "maquina=$MAQUINA"; then
        if [ "$horas" -gt $((24 * DIAS_SIN_INTERNET)) ]; then
            salir "${AVISO}Hace más de $DIAS_SIN_INTERNET días que no se puede revisar la suscripción del usuario (sin internet o el servidor no responde). Dile, en español, que se conecte a internet y vuelva a abrir Claude. Hasta que se revise, no uses los comandos de la versión mejorada." 0
        fi
        salir '' 0
    fi
    ok="$(j get "$TMPD/r.json" ok)"; motivo="$(j get "$TMPD/r.json" motivo)"
    if [ "$ok" = true ]; then
        j set "$LICENCIA" ultima_ok "$(ahora)" vence "$(j get "$TMPD/r.json" vence)"
        rv="$(j get "$TMPD/r.json" version)"; rs="$(j get "$TMPD/r.json" sha)"; is="$(j get "$INSTALADO" sha)"
        if [ -f "$INSTALADO" ] && [ -n "$rv" ] && [ -n "$rs" ] && [ "$rs" != "$is" ]; then
            salir "${AVISO}Hay una versión nueva ($rv); el usuario tiene la $(j get "$INSTALADO" version). Si es buen momento, ofrécele correr /animaciones-ia:actualizar." 0
        fi
        salir '' 0
    fi
    if [ "$(j get "$TMPD/r.json" revertir)" = true ]; then
        res="$(volver_gratis "$motivo")"
        salir "${AVISO}La versión mejorada ya no está vigente: $motivo $res Díselo al usuario en español, con calma: que cierre y vuelva a abrir Claude, que sigue teniendo la versión gratis, y que si renueva en Skool le escriba a David. No uses los comandos de la versión mejorada en esta sesión." 0
    fi
    salir "${AVISO}Aviso sobre la suscripción: $motivo" 0
fi

# ---------- activar / actualizar ----------
if [ "$ACCION" = activar ]; then
    CODIGO="$(printf '%s' "$CODIGO" | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')"
    printf '%s' "$CODIGO" | grep -Eq '^FAB-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$' || salir 'ERROR: el código debe verse así: FAB-XXXX-XXXX-XXXX (cópialo completo del mensaje de David).' 2
else
    CODIGO="$(j get "$LICENCIA" codigo)"
    [ -n "$CODIGO" ] || salir 'ERROR: esta computadora no tiene código guardado. Primero: activar TU-CODIGO' 2
fi

echo 'Revisando tu código...'
pedir "$TMPD/info.json" 3 360 accion=info "codigo=$CODIGO" "maquina=$MAQUINA" || salir "NO SE PUDO: no pude hablar con el servidor ($(head -c 300 "$TMPD/curl_err" 2>/dev/null)). Revisa tu internet y vuelve a intentar." 4
I="$TMPD/info.json"
if [ "$(j get "$I" ok)" != true ]; then
    motivo="$(j get "$I" motivo)"; [ -n "$motivo" ] || motivo="el servidor respondió algo inesperado: $(head -c 200 "$I")"
    if [ "$ACCION" = actualizar ] && [ "$(j get "$I" revertir)" = true ] && [ -f "$INSTALADO" ]; then
        res="$(volver_gratis "$motivo")"; salir "NO SE PUDO: $motivo
$res" 3
    fi
    salir "NO SE PUDO: $motivo" 3
fi
VERSION="$(j get "$I" version)"; SHA="$(j get "$I" sha)"; PARTES="$(j get "$I" partes)"; BYTES="$(j get "$I" bytes)"
rm -f "$LICENCIA"; j set "$LICENCIA" codigo "$CODIGO" ultima_ok "$(ahora)" vence "$(j get "$I" vence)"

if [ "$ACCION" = actualizar ] && [ -f "$INSTALADO" ] && [ "$(j get "$INSTALADO" sha)" = "$SHA" ] && [ -f "$DESTINO/.claude-plugin/marketplace.json" ]; then
    if [ -z "$CLAUDE_EXE" ] || [ "$(version_en_claude)" = "$VERSION" ]; then salir "Ya tienes la última versión ($VERSION). No hay nada que actualizar." 0; fi
fi

MB="$(awk -v b="${BYTES:-0}" 'BEGIN{printf "%.1f", b/1048576}')"
echo "Hola $(j get "$I" nombre). Bajando animaciones-ia $VERSION, versión mejorada ($MB MB en $PARTES partes)..."
NUEVO="$DATOS/descarga_$$/plugin"
rm -rf "$DATOS/descarga_$$"; mkdir -p "$NUEVO"
fallo() { rm -rf "$DATOS/descarga_$$"; salir "NO SE PUDO: $1" 4; }
n=0
while [ "$n" -lt "${PARTES:-0}" ]; do
    pedir "$TMPD/p.json" 3 360 accion=parte "codigo=$CODIGO" "maquina=$MAQUINA" "sha=$SHA" "n=$n" || fallo "no pude bajar la parte $((n + 1)). Revisa tu internet y vuelve a intentar."
    [ "$(j get "$TMPD/p.json" ok)" = true ] || fallo "$(j get "$TMPD/p.json" motivo)"
    [ "$(j b64 "$TMPD/p.json" datos "$TMPD/parte.zip")" = si ] || fallo "la parte $((n + 1)) llegó dañada."
    unzip -oq "$TMPD/parte.zip" -d "$NUEVO" || fallo "no pude abrir la parte $((n + 1))."
    rm -f "$TMPD/parte.zip" "$TMPD/p.json"
    echo "  parte $((n + 1))/$PARTES lista"
    n=$((n + 1))
done
[ -f "$NUEVO/.claude-plugin/marketplace.json" ] || fallo 'La descarga llegó incompleta (falta marketplace.json).'
# reemplazo: la versión anterior queda como respaldo hasta la siguiente actualización
rm -rf "$ANTERIOR"
[ -d "$DESTINO" ] && mv "$DESTINO" "$ANTERIOR"
mv "$NUEVO" "$DESTINO" || fallo 'no pude mover la versión nueva a su lugar.'
rm -rf "$DATOS/descarga_$$"
rm -f "$INSTALADO"; j set "$INSTALADO" version "$VERSION" sha "$SHA" fecha "$(date '+%Y-%m-%d %H:%M')"

if [ -n "$CLAUDE_EXE" ]; then
    v="$(usar_fuente "$DESTINO" 1 2>"$TMPD/err.txt")"
    [ "$v" = "$VERSION" ] && salir "LISTO: animaciones-ia $VERSION (versión mejorada) instalada. Cierra y vuelve a abrir Claude para usarla (/animaciones-ia:preparar)." 0
    echo "DESCARGADO: animaciones-ia $VERSION en $DESTINO, pero Claude no la tomó sola. $(cat "$TMPD/err.txt" 2>/dev/null)"
else
    echo "DESCARGADO: animaciones-ia $VERSION en $DESTINO"
fi
echo "FALTA_REGISTRAR: en la Terminal corre  claude plugin marketplace remove $MK  luego  claude plugin marketplace add \"$DESTINO\"  y luego  claude plugin install $PLUGIN"
