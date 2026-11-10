# animaciones-ia: pasa de la versión gratis a la completa (alumnos) con tu código personal, la actualiza
# y revisa que tu suscripción siga vigente. Si ya no lo está, regresa sola a la versión gratis.
#   powershell -NoProfile -ExecutionPolicy Bypass -File fabrica.ps1 activar FAB-XXXX-XXXX-XXXX
#   powershell -NoProfile -ExecutionPolicy Bypass -File fabrica.ps1 actualizar | estado | revisar | volver-gratis
# No necesita GitHub: le pregunta al servidor de David si tu código es válido y baja la versión mejorada.
param(
    [Parameter(Position = 0)][ValidateSet('activar', 'actualizar', 'estado', 'revisar', 'volver-gratis')][string]$Accion = 'estado',
    [Parameter(Position = 1)][string]$Codigo = ''
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$SERVIDOR = 'https://script.google.com/macros/s/AKfycbwNhtbg-iKdQPmxslWXqxeHjZdDhSoaRdlrPHrvzUaQw_RyT0niQTCYzrogKQ8j6uV_/exec'
$MK = 'animaciones-con-ia'                    # el mismo marketplace y el mismo plugin para la gratis y la completa
$PLUGIN = 'animaciones-ia@animaciones-con-ia'
$REPO_GRATIS = 'davidviraliza/animaciones-ia'
$REVISAR_CADA_HORAS = 24                      # cada cuánto pregunta si la suscripción sigue vigente
$DIAS_SIN_INTERNET = 10                       # tolerancia sin poder revisar

$datos = if ($env:FABRICA_IA_DATOS) { $env:FABRICA_IA_DATOS } else { Join-Path $env:LOCALAPPDATA 'fabrica-ia' }
New-Item -ItemType Directory -Force -Path $datos | Out-Null
$licencia = Join-Path $datos 'licencia.json'
$instalado = Join-Path $datos 'plugin_instalado.json'
$destino = Join-Path $datos 'plugin'
$anterior = Join-Path $datos 'plugin_anterior'

function Salir($texto, $codigoSalida) { if ($texto) { Write-Output $texto }; exit $codigoSalida }
function LeerJson($ruta) { if (Test-Path $ruta) { try { return (Get-Content $ruta -Raw -Encoding UTF8 | ConvertFrom-Json) } catch {} }; return $null }
function GuardarJson($ruta, $obj) { $obj | ConvertTo-Json | Set-Content -Path $ruta -Encoding UTF8 }
function Borrar($d) {                         # también con rutas largas (> 260 letras)
    if (-not (Test-Path -LiteralPath $d)) { return }
    try { Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction Stop } catch { Remove-Item -LiteralPath ('\\?\' + (Resolve-Path -LiteralPath $d).Path) -Recurse -Force -ErrorAction SilentlyContinue }
}
function Ahora { (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss') }

# Identificador de esta PC (no es personal: un resumen de nombre de equipo + usuario)
$sha = [Security.Cryptography.SHA256]::Create()
$maquina = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes("$env:COMPUTERNAME|$env:USERNAME"))[0..7] | ForEach-Object { $_.ToString('x2') })

function Pedir($params, $intentos = 3, $espera = 360) {
    $q = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$([Uri]::EscapeDataString([string]$_.Value))" }) -join '&'
    for ($i = 1; $i -le $intentos; $i++) {
        try { return Invoke-RestMethod -Uri "$SERVIDOR`?$q" -Method Get -TimeoutSec $espera -UseBasicParsing }
        catch { if ($i -eq $intentos) { throw "No pude hablar con el servidor ($($_.Exception.Message)). Revisa tu internet y vuelve a intentar." }; Start-Sleep -Seconds (5 * $i) }
    }
}

# ---------- Claude Code (comando claude) ----------
# Quien solo usa la app de escritorio no tiene «claude» en el PATH: la app trae su propio claude.exe.
function BuscarClaude {
    $c = Get-Command claude -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return $c.Source }
    if ($env:CLAUDE_PID) {                                   # el Claude que nos está corriendo ahora mismo
        try { $p = (Get-Process -Id $env:CLAUDE_PID -ErrorAction Stop).Path; if ($p -and (Split-Path $p -Leaf) -match '^claude(\.exe)?$') { return $p } } catch {}
    }
    $raices = @("$env:LOCALAPPDATA\Claude-Data", "$env:APPDATA\Claude\claude-code", "$env:LOCALAPPDATA\AnthropicClaude", "$env:USERPROFILE\.local\bin") | Where-Object { Test-Path $_ }
    $e = $raices | ForEach-Object { Get-ChildItem -Path $_ -Filter claude.exe -Recurse -Depth 5 -ErrorAction SilentlyContinue } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($e) { return $e.FullName }
    return $null
}
$CLAUDE_EXE = if ($env:FABRICA_IA_SIN_REGISTRAR) { $null } else { BuscarClaude }
$hayClaude = [bool]$CLAUDE_EXE
function ClaudeCmd([string[]]$a) {
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $s = (& $CLAUDE_EXE @a 2>&1 | ForEach-Object { "$_" }) -join "`n"; return @{ ok = ($LASTEXITCODE -eq 0); texto = $s } }
    finally { $ErrorActionPreference = $prev }
}
function CliJson([string[]]$a) {
    $r = ClaudeCmd $a; $t = $r.texto; $i = $t.IndexOf('[')
    if ($i -lt 0) { return @() }
    try { return @($t.Substring($i) | ConvertFrom-Json) } catch { return @() }
}
function VersionEnClaude {
    $p = CliJson @('plugin', 'list', '--json') | Where-Object { $_.id -eq $PLUGIN -or "$($_.name)@$($_.marketplace)" -eq $PLUGIN } | Select-Object -First 1
    if ($p) { return [string]$p.version }; return ''
}
function UsarFuente($fuente, $esCarpeta) {
    # Cambia de dónde sale animaciones-ia (GitHub = gratis, carpeta local = completa) y lo deja instalado.
    $mks = CliJson @('plugin', 'marketplace', 'list', '--json')
    if ($mks | Where-Object { $_.name -eq 'fabrica-ia' }) {          # el plugin aparte de antes: ya no se usa
        ClaudeCmd @('plugin', 'uninstall', 'fabrica-ia@fabrica-ia') | Out-Null
        ClaudeCmd @('plugin', 'marketplace', 'remove', 'fabrica-ia') | Out-Null
    }
    $act = $mks | Where-Object { $_.name -eq $MK } | Select-Object -First 1
    $mismo = $act -and ((-not $esCarpeta -and $act.repo -eq $fuente) -or ($esCarpeta -and $act.path -and ((Resolve-Path $act.path -ErrorAction SilentlyContinue).Path -eq (Resolve-Path $fuente).Path)))
    if ($mismo) { ClaudeCmd @('plugin', 'marketplace', 'update', $MK) | Out-Null }
    else {
        if ($act) { ClaudeCmd @('plugin', 'marketplace', 'remove', $MK) | Out-Null }
        $r = ClaudeCmd @('plugin', 'marketplace', 'add', $fuente)
        if (-not $r.ok) { throw "Claude no aceptó la fuente del plugin: $($r.texto)" }
    }
    $r = ClaudeCmd @('plugin', 'install', $PLUGIN)
    if (-not $r.ok -or $r.texto -match 'already') { ClaudeCmd @('plugin', 'update', $PLUGIN) | Out-Null }
    ClaudeCmd @('plugin', 'enable', $PLUGIN) | Out-Null
    return (VersionEnClaude)
}

function VolverGratis($motivo) {
    # Quita la versión mejorada de esta PC y deja la gratis. Tus videos, voces y reglas no se tocan.
    foreach ($d in @($destino, $anterior)) { Borrar $d }
    if (Test-Path $instalado) { Remove-Item $instalado -Force }
    $lic = LeerJson $licencia
    if ($lic) { $lic | Add-Member -NotePropertyName terminado -NotePropertyValue (Ahora) -Force; $lic | Add-Member -NotePropertyName motivo -NotePropertyValue $motivo -Force; GuardarJson $licencia $lic }
    if ($hayClaude) {
        try { $v = UsarFuente $REPO_GRATIS $false } catch { $v = '' }
        if ($v) { return "VERSION_GRATIS: se regresó a animaciones-ia $v (gratis)." }
        return "VERSION_GRATIS: se quitó la versión mejorada. Si animaciones-ia no aparece, en Claude escribe  /plugin marketplace add $REPO_GRATIS  y  /plugin install $PLUGIN"
    }
    return 'VERSION_GRATIS: se quitó la versión mejorada de esta PC.'
}

# ---------- estado ----------
if ($Accion -eq 'estado') {
    $i = LeerJson $instalado; $lic = LeerJson $licencia
    if (-not $i) { Salir 'animaciones-ia versión mejorada: no está activada en esta PC (tienes la gratis). Usa: activar TU-CODIGO' 1 }
    $v = if ($lic -and $lic.vence) { " Suscripción vigente hasta el $($lic.vence)." } else { '' }
    $u = if ($lic -and $lic.ultima_ok) { " Última revisión: $($lic.ultima_ok)." } else { '' }
    Salir "animaciones-ia $($i.version) (versión mejorada) instalada el $($i.fecha).$v$u" 0
}

# ---------- volver-gratis (a mano) ----------
if ($Accion -eq 'volver-gratis') { Salir (VolverGratis 'a petición del usuario') 0 }

# ---------- revisar (al abrir Claude; lo corre el hook de la versión mejorada) ----------
if ($Accion -eq 'revisar') {
    $lic = LeerJson $licencia
    $aviso = '[animaciones-ia] '
    if (-not $lic -or -not $lic.codigo) {
        $r = VolverGratis 'sin código en esta PC'
        Salir ($aviso + "Esta PC no tiene código de alumno, así que la versión mejorada no puede usarse aquí. $r Dile al usuario, en español, que cierre y vuelva a abrir Claude, y que si es alumno use /animaciones-ia:activar con su código. No uses los comandos de la versión mejorada en esta sesión.") 0
    }
    if ($lic.ultima_ok) {
        try { $horas = ((Get-Date) - [datetime]$lic.ultima_ok).TotalHours } catch { $horas = 9999 }
        if ($horas -lt $REVISAR_CADA_HORAS) { Salir '' 0 }
    } else { $horas = 9999 }
    try { $r = Pedir @{ accion = 'estado'; codigo = $lic.codigo; maquina = $maquina } 1 20 }
    catch {
        if ($horas -gt 24 * $DIAS_SIN_INTERNET) {
            Salir ($aviso + "Hace más de $DIAS_SIN_INTERNET días que no se puede revisar la suscripción del usuario (sin internet o el servidor no responde). Dile, en español, que se conecte a internet y vuelva a abrir Claude. Hasta que se revise, no uses los comandos de la versión mejorada.") 0
        }
        Salir '' 0
    }
    if ($r.ok) {
        $lic | Add-Member -NotePropertyName ultima_ok -NotePropertyValue (Ahora) -Force
        $lic | Add-Member -NotePropertyName vence -NotePropertyValue ([string]$r.vence) -Force
        GuardarJson $licencia $lic
        $i = LeerJson $instalado
        if ($i -and $r.version -and $r.sha -and $r.sha -ne $i.sha) { Salir ($aviso + "Hay una versión nueva ($($r.version)); el usuario tiene la $($i.version). Si es buen momento, ofrécele correr /animaciones-ia:actualizar.") 0 }
        Salir '' 0
    }
    if ($r.revertir) {
        $res = VolverGratis ([string]$r.motivo)
        Salir ($aviso + "La versión mejorada ya no está vigente: $($r.motivo) $res Díselo al usuario en español, con calma: que cierre y vuelva a abrir Claude, que sigue teniendo la versión gratis, y que si renueva en Skool le escriba a David. No uses los comandos de la versión mejorada en esta sesión.") 0
    }
    Salir ($aviso + "Aviso sobre la suscripción: $($r.motivo)") 0
}

# ---------- activar / actualizar ----------
if ($Accion -eq 'activar') {
    $Codigo = $Codigo.Trim().ToUpper()
    if ($Codigo -notmatch '^FAB-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$') { Salir 'ERROR: el código debe verse así: FAB-XXXX-XXXX-XXXX (cópialo completo del mensaje de David).' 2 }
} else {
    $lic = LeerJson $licencia
    if (-not $lic -or -not $lic.codigo) { Salir 'ERROR: esta PC no tiene código guardado. Primero: activar TU-CODIGO' 2 }
    $Codigo = $lic.codigo
}

Write-Output 'Revisando tu código...'
$info = Pedir @{ accion = 'info'; codigo = $Codigo; maquina = $maquina }
if (-not $info.ok) {
    if ($Accion -eq 'actualizar' -and $info.revertir -and (Test-Path $instalado)) { $res = VolverGratis ([string]$info.motivo); Salir "NO SE PUDO: $($info.motivo)`n$res" 3 }
    Salir "NO SE PUDO: $($info.motivo)" 3
}
GuardarJson $licencia ([pscustomobject]@{ codigo = $Codigo; ultima_ok = (Ahora); vence = [string]$info.vence })

if ($Accion -eq 'actualizar' -and (Test-Path $instalado)) {
    $prev = LeerJson $instalado
    if ($prev.sha -eq $info.sha -and (Test-Path (Join-Path $destino '.claude-plugin\marketplace.json'))) {
        if (-not $hayClaude -or (VersionEnClaude) -eq $info.version) { Salir "Ya tienes la última versión ($($info.version)). No hay nada que actualizar." 0 }
    }
}

Write-Output "Hola $($info.nombre). Bajando animaciones-ia $($info.version), versión mejorada ($([math]::Round($info.bytes / 1MB, 1)) MB en $($info.partes) partes)..."
$tmp = Join-Path $datos ('descarga_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$nuevo = Join-Path $tmp 'plugin'
New-Item -ItemType Directory -Force -Path $nuevo | Out-Null
try {
    for ($n = 0; $n -lt $info.partes; $n++) {
        $r = Pedir @{ accion = 'parte'; codigo = $Codigo; maquina = $maquina; sha = $info.sha; n = $n }
        if (-not $r.ok) { throw $r.motivo }
        $zip = Join-Path $tmp "parte_$n.zip"
        [IO.File]::WriteAllBytes($zip, [Convert]::FromBase64String($r.datos))
        Expand-Archive -Path $zip -DestinationPath $nuevo -Force
        Remove-Item $zip -Force
        Write-Output "  parte $($n + 1)/$($info.partes) lista"
    }
    if (-not (Test-Path (Join-Path $nuevo '.claude-plugin\marketplace.json'))) { throw 'La descarga llegó incompleta (falta marketplace.json).' }
    # el zip del servidor quita la marca UTF-8 (BOM); sin ella PowerShell 5 lee mal los acentos de los .ps1
    Get-ChildItem -Path $nuevo -Recurse -Filter *.ps1 | ForEach-Object {
        $b = [IO.File]::ReadAllBytes($_.FullName)
        if (-not ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)) { [IO.File]::WriteAllBytes($_.FullName, [byte[]](0xEF, 0xBB, 0xBF) + $b) }
    }
    # reemplazo: la versión anterior queda como respaldo hasta la siguiente actualización
    Borrar $anterior
    if (Test-Path $destino) { Move-Item $destino $anterior }
    Move-Item $nuevo $destino
} catch {
    Borrar $tmp
    Salir "NO SE PUDO: $($_.Exception.Message)" 4
}
Borrar $tmp
GuardarJson $instalado ([pscustomobject]@{ version = $info.version; sha = $info.sha; fecha = (Get-Date -Format 'yyyy-MM-dd HH:mm') })

if ($hayClaude) {
    try { $v = UsarFuente $destino $true } catch { $v = ''; $err = $_.Exception.Message }
    if ($v -eq $info.version) { Salir "LISTO: animaciones-ia $($info.version) (versión mejorada) instalada. Cierra y vuelve a abrir Claude para usarla (/animaciones-ia:preparar)." 0 }
    Write-Output "DESCARGADO: animaciones-ia $($info.version) en $destino, pero Claude no la tomó sola. $err"
} else {
    Write-Output "DESCARGADO: animaciones-ia $($info.version) en $destino"
}
Write-Output "FALTA_REGISTRAR: en Claude escribe  /plugin marketplace remove $MK  luego  /plugin marketplace add $destino  y luego  /plugin install $PLUGIN"
