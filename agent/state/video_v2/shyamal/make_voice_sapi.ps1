# PREVIEW voice only (Windows built-in Zira). Real voice = the owner's ElevenLabs MP3. Makes one WAV per scene in .\voice\
param([string]$ScriptJson = "script_en.json", [string]$Voice = "Microsoft Zira Desktop", [int]$Rate = -1)
Add-Type -AssemblyName System.Speech
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg = Get-Content (Join-Path $here $ScriptJson) -Raw -Encoding UTF8 | ConvertFrom-Json
$out = Join-Path $here "voice"
New-Item -ItemType Directory -Force $out | Out-Null
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice($Voice)
$s.Rate = $Rate
foreach ($sc in $cfg.scenes) {
    $f = Join-Path $out ("s{0}.wav" -f $sc.id)
    $s.SetOutputToWaveFile($f)
    $s.Speak($sc.voice)
    $s.SetOutputToNull()
    Write-Output ("scene {0} -> {1}" -f $sc.id, $f)
}
$s.Dispose()
