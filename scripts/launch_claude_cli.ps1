#!/usr/bin/env pwsh
<#
launch_claude_cli.ps1
Usage: launch_claude_cli.ps1 <provider> [-- other args]
Providers: pro, bedrock
This script loads provider config from the scripts folder, sets environment variables, then invokes the configured Claude CLI command.
#>
param(
    [Parameter(Mandatory=$true)][ValidateSet('pro','bedrock')][string]$Provider,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

function Load-JsonFile($path) {
    if (Test-Path $path) { Get-Content $path -Raw | ConvertFrom-Json } else { return $null }
}

if ($Provider -eq 'pro') {
    $cfg = Load-JsonFile (Join-Path $scriptDir 'claude_pro_config.json')
    if ($cfg -and $cfg.api_key) { $env:CLAUDE_API_KEY = $cfg.api_key }
    $cmd = if ($cfg -and $cfg.claude_cli_cmd) { $cfg.claude_cli_cmd } else { 'claude' }
    $args = $RemainingArgs
} else {
    # bedrock
    $cfg = Load-JsonFile (Join-Path $scriptDir 'bedrock_config.json')
    if ($cfg -and $cfg.aws_access_key_id -and $cfg.aws_secret_access_key) {
        $env:AWS_ACCESS_KEY_ID = $cfg.aws_access_key_id
        $env:AWS_SECRET_ACCESS_KEY = $cfg.aws_secret_access_key
    }
    if ($cfg -and $cfg.aws_profile) { $env:AWS_PROFILE = $cfg.aws_profile }
    if ($cfg -and $cfg.aws_region) { $env:AWS_REGION = $cfg.aws_region }
    $cmd = if ($cfg -and $cfg.claude_cli_cmd) { $cfg.claude_cli_cmd } else { 'claude' }
    # add provider flag for CLIs that accept it; adjust if your CLI needs different flags
    $args = @('--provider','bedrock') + $RemainingArgs
}

Write-Host "Launching CLI: $cmd with args: $($args -join ' ')" -ForegroundColor Green

try {
    & $cmd @args
} catch {
    Write-Error "Failed to launch $cmd. Make sure the CLI is installed and available in PATH. Error: $_"
}
