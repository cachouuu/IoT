param([Parameter(ValueFromRemainingArguments=$true)][string[]]$OpenSpecArgs)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$localCli = Join-Path $taskRoot 'node_modules/@fission-ai/openspec/bin/openspec.js'
$workspaceCli = [IO.Path]::GetFullPath((Join-Path $taskRoot '../../../tmp/dic3-openspec/node_modules/@fission-ai/openspec/bin/openspec.js'))
$cli = if (Test-Path -LiteralPath $localCli) { $localCli } elseif (Test-Path -LiteralPath $workspaceCli) { $workspaceCli } else { throw 'Run npm install in the submission directory first.' }
$env:OPENSPEC_TELEMETRY = '0'
$env:OPENSPEC_NO_UPDATE_CHECK = '1'
Push-Location $taskRoot
try { & node $cli @OpenSpecArgs; $taskExitCode=$LASTEXITCODE } finally { Pop-Location }
exit $taskExitCode
