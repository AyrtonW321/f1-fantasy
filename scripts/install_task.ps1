$ErrorActionPreference = 'Stop'

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($null -eq $uv -or [string]::IsNullOrWhiteSpace($uv.Source)) {
    throw 'uv.exe was not found on PATH. Install uv or add uv.exe to PATH, then rerun this script.'
}

$taskName = 'F1FantasyWeekly'
$repoRoot = Split-Path $PSScriptRoot -Parent
$arguments = 'run python -m pipelines.weekly_update'
$action = New-ScheduledTaskAction -Execute $uv.Source -Argument $arguments -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours(20))
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal `
    -Description 'Run the F1 Fantasy weekly update daily at 20:00 local time.' -Force | Out-Null

$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "Task: $taskName"
Write-Host "Next run: $($info.NextRunTime)"
Write-Host "Command: `"$($uv.Source)`" $arguments"
Write-Host "Working directory: $repoRoot"
