[CmdletBinding()]
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = (Get-Command python -ErrorAction Stop).Source
$taskName = 'NEXUS Local Learning Worker'
$workerScript = Join-Path $projectRoot 'scripts/run-worker.ps1'

if (-not $Apply) {
    Write-Output "Pronto para registrar '$taskName' no logon deste usuário."
    Write-Output 'Nenhuma tarefa foi criada. Para ativar deliberadamente, execute este script com -Apply.'
    Write-Output "Projeto: $projectRoot"
    exit 0
}

$action = New-ScheduledTaskAction -Execute $python `
    -Argument ('-m nexus_learning --db nexus_learning.db worker --poll 2') `
    -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Description 'N.E.X.U.S. local bounded learning worker' -Force | Out-Null
Write-Output "Tarefa '$taskName' registrada para o usuário atual."
Write-Output 'O worker só usa a API externa quando as permissões e limites locais estiverem habilitados.'
