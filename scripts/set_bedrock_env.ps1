# set_bedrock_env.ps1 (robust)
# Reads bedrock_config.json and persistently sets AWS_BEARER_TOKEN_BEDROCK and AWS_REGION using setx
$cfgPath = Join-Path $PSScriptRoot 'bedrock_config.json'
$raw = Get-Content -Raw -Path $cfgPath
$ht = ConvertFrom-Json -AsHashtable $raw
# build case-insensitive map
$ci = @{}
foreach ($k in $ht.Keys) { $ci[$k.ToLower()] = $ht[$k] }
$token = $null; if ($ci.ContainsKey('aws_bearer_token_bedrock')) { $token = $ci['aws_bearer_token_bedrock'] }
if ($token -and $token -ne '') { setx AWS_BEARER_TOKEN_BEDROCK $token -m | Out-Null; Write-Host 'Set AWS_BEARER_TOKEN_BEDROCK via setx' } else { Write-Host 'No AWS_BEARER_TOKEN_BEDROCK found in config' }
$region = $null; if ($ci.ContainsKey('aws_region')) { $region = $ci['aws_region'] }
if ($region -and $region -ne '') { setx AWS_REGION $region -m | Out-Null; Write-Host 'Set AWS_REGION via setx' } else { Write-Host 'No AWS_REGION found in config' }
Write-Host 'Note: setx affects new processes. To use in current session, run: $env:AWS_BEARER_TOKEN_BEDROCK = "<token>"; $env:AWS_REGION = "<region>"'
