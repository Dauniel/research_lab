# Keep the system + display awake for long GPU runs.
# Usage: powershell.exe -ExecutionPolicy Bypass -File spring_implementation\keep_awake.ps1
# Stop:  Ctrl-C in the window, or close the window. State auto-reverts on exit.

$signature = @"
[DllImport("kernel32.dll", SetLastError=true)]
public static extern uint SetThreadExecutionState(uint esFlags);
"@
$type = Add-Type -MemberDefinition $signature -Name "PowerUtil" -Namespace "KeepAwake" -PassThru

$ES_CONTINUOUS       = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED  = [uint32]"0x00000001"
$ES_DISPLAY_REQUIRED = [uint32]"0x00000002"

$flags = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED
$prev = $type::SetThreadExecutionState($flags)

Write-Host ("Keep-awake active at {0}. PID={1}." -f (Get-Date), $PID)
Write-Host "Press Ctrl-C or close this window to stop."

try {
    while ($true) { Start-Sleep -Seconds 60 }
}
finally {
    [void]$type::SetThreadExecutionState($ES_CONTINUOUS)
    Write-Host "Keep-awake released."
}
