# Activa o actualiza fabrica-ia (el plugin completo para alumnos) con tu código personal.
#   powershell -NoProfile -ExecutionPolicy Bypass -File fabrica.ps1 activar FAB-XXXX-XXXX-XXXX
#   powershell -NoProfile -ExecutionPolicy Bypass -File fabrica.ps1 actualizar
# No necesita GitHub: le pregunta al servidor de David si tu código es válido y baja el plugin.
param(
    [Parameter(Position = 0)][ValidateSet('activar', 'actualizar', 'estado')][string]$Accion = 'estado',
    [Parameter(Position = 1)][string]$Codigo = ''
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$SERVIDOR = 'https://script.google.com/macros/s/AKfycbwNhtbg-iKdQPmxslWXqxeHjZdDhSoaRdlrPHrvzUaQw_RyT0niQTCYzrogKQ8j6uV_/exec'

$datos = if ($env:FABRICA_IA_DATOS) { $env:FABRICA_IA_DATOS } else { Join-Path $env:LOCALAPPDATA 'fabrica-ia' }
New-Item -ItemType Directory -Force -Path $datos | Out-Null
$licencia = Join-Path $datos 'licencia.json'
$instalado = Join-Path $datos 'plugin_instalado.json'
$destino = Join-Path $datos 'plugin'

function Salir($texto, $codigoSalida) { Write-Output $texto; exit $codigoSalida }

# Identificador de esta PC (no es personal: un resumen de nombre de equipo + usuario)
$sha = [Security.Cryptography.SHA256]::Create()
$maquina = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes("$env:COMPUTERNAME|$env:USERNAME"))[0..7] | ForEach-Object { $_.ToString('x2') })

if ($Accion -eq 'estado') {
    if (Test-Path $instalado) { $i = Get-Content $instalado -Raw | ConvertFrom-Json; Salir "fabrica-ia $($i.version) instalado el $($i.fecha) en $destino" 0 }
    Salir 'fabrica-ia todavía no está activado en esta PC. Usa: activar TU-CODIGO' 1
}

if ($Accion -eq 'activar') {
    $Codigo = $Codigo.Trim().ToUpper()
    if ($Codigo -notmatch '^FAB-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$') { Salir 'ERROR: el código debe verse así: FAB-XXXX-XXXX-XXXX (cópialo completo del mensaje de David).' 2 }
} else {
    if (-not (Test-Path $licencia)) { Salir 'ERROR: esta PC no tiene código guardado. Primero: activar TU-CODIGO' 2 }
    $Codigo = (Get-Content $licencia -Raw | ConvertFrom-Json).codigo
}

function Pedir($params) {
    $q = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$([Uri]::EscapeDataString([string]$_.Value))" }) -join '&'
    for ($intento = 1; $intento -le 3; $intento++) {
        try { return Invoke-RestMethod -Uri "$SERVIDOR`?$q" -Method Get -TimeoutSec 360 -UseBasicParsing }
        catch { if ($intento -eq 3) { throw "No pude hablar con el servidor ($($_.Exception.Message)). Revisa tu internet y vuelve a intentar." }; Start-Sleep -Seconds (5 * $intento) }
    }
}

Write-Output 'Revisando tu código...'
$info = Pedir @{ accion = 'info'; codigo = $Codigo; maquina = $maquina }
if (-not $info.ok) { Salir "NO SE PUDO: $($info.motivo)" 3 }
@{ codigo = $Codigo } | ConvertTo-Json | Set-Content -Path $licencia -Encoding UTF8

if ($Accion -eq 'actualizar' -and (Test-Path $instalado)) {
    $prev = Get-Content $instalado -Raw | ConvertFrom-Json
    if ($prev.sha -eq $info.sha -and (Test-Path (Join-Path $destino '.claude-plugin\marketplace.json'))) { Salir "Ya tienes la última versión ($($info.version)). No hay nada que actualizar." 0 }
}

Write-Output "Hola $($info.nombre). Bajando fabrica-ia $($info.version) ($([math]::Round($info.bytes / 1MB, 1)) MB en $($info.partes) partes)..."
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
    # reemplazo: la versión anterior queda como respaldo hasta la siguiente actualización
    $anterior = Join-Path $datos 'plugin_anterior'
    if (Test-Path $anterior) { Remove-Item $anterior -Recurse -Force }
    if (Test-Path $destino) { Move-Item $destino $anterior }
    Move-Item $nuevo $destino
} catch {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Salir "NO SE PUDO: $($_.Exception.Message)" 4
}
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
@{ version = $info.version; sha = $info.sha; fecha = (Get-Date -Format 'yyyy-MM-dd HH:mm') } | ConvertTo-Json | Set-Content -Path $instalado -Encoding UTF8

# Registrar en Claude Code (si el comando claude está disponible)
$claude = if ($env:FABRICA_IA_SIN_REGISTRAR) { $null } else { Get-Command claude -ErrorAction SilentlyContinue }
if ($claude) {
    $lista = (& claude plugin marketplace list 2>&1 | Out-String)
    if ($lista -match 'fabrica-ia') { & claude plugin marketplace update fabrica-ia 2>&1 | Out-Null }
    else { & claude plugin marketplace add "$destino" 2>&1 | Out-Null }
    $plugins = (& claude plugin list 2>&1 | Out-String)
    if ($plugins -match 'fabrica-ia@fabrica-ia') { & claude plugin update fabrica-ia@fabrica-ia 2>&1 | Out-Null }
    else { & claude plugin install fabrica-ia@fabrica-ia 2>&1 | Out-Null }
    Write-Output "LISTO: fabrica-ia $($info.version) instalado. Cierra y vuelve a abrir Claude para usarlo (/fabrica-ia:preparar)."
} else {
    Write-Output "DESCARGADO: fabrica-ia $($info.version) en $destino"
    Write-Output "FALTA_REGISTRAR: en Claude escribe  /plugin marketplace add $destino  y luego  /plugin install fabrica-ia@fabrica-ia"
}
