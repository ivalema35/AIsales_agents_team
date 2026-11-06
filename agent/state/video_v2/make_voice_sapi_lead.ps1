# PREVIEW voice only (Windows built-in Zira). Real voice = the owner's ElevenLabs MP3. Usage: powershell -File make_voice_sapi_lead.ps1 -Key vistara
# Reads <key>\voice_script_elevenlabs.txt (6 scene lines separated by <break .../> lines) and makes <key>\voice\s1.wav .. s6.wav
param([Parameter(Mandatory = $true)][string]$Key, [string]$Voice = "Microsoft Zira Desktop", [int]$Rate = -1)
Add-Type -AssemblyName System.Speech
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$dir = Join-Path $here $Key
$lines = Get-Content (Join-Path $dir "voice_script_elevenlabs.txt") -Encoding UTF8 | Where-Object { $_.Trim() -ne "" -and $_ -notmatch "^\s*<break" }
if ($lines.Count -ne 6) { throw "expected 6 scene lines, found $($lines.Count)" }
$out = Join-Path $dir "voice"
New-Item -ItemType Directory -Force $out | Out-Null
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice($Voice)
$s.Rate = $Rate
for ($i = 0; $i -lt 6; $i++) {
    $f = Join-Path $out ("s{0}.wav" -f ($i + 1))
    $s.SetOutputToWaveFile($f)
    $s.Speak($lines[$i])
    $s.SetOutputToNull()
    Write-Output ("scene {0} -> {1}" -f ($i + 1), $f)
}
$s.Dispose()
