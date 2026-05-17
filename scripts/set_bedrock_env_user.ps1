# set_bedrock_env_user.ps1
# Reads bedrock_config.json and sets AWS_BEARER_TOKEN_BEDROCK and AWS_REGION for current user using setx (no -m)
$cfgPath = Join-Path $PSScriptRoot 'bedrock_config.json'
$raw = Get-Content -Raw -Path $cfgPath
$ht = ConvertFrom-Json -AsHashtable $raw
$ci = @{}
foreach ($k in $ht.Keys) { $ci[$k.ToLower()] = $ht[$k] }
$token = $null; if ($ci.ContainsKey('aws_bearer_token_bedrock')) { $token = $ci['aws_bearer_token_bedrock'] }
if ($token -and $token -ne '') { setx AWS_BEARER_TOKEN_BEDROCK $token | Out-Null; Write-Host 'Set AWS_BEARER_TOKEN_BEDROCK via setx (user level)'} else { Write-Host 'No AWS_BEARER_TOKEN_BEDROCK found in config' }
$region = $null; if ($ci.ContainsKey('aws_region')) { $region = $ci['aws_region'] }
if ($region -and $region -ne '') { setx AWS_REGION $region | Out-Null; Write-Host 'Set AWS_REGION via setx (user level)'} else { Write-Host 'No AWS_REGION found in config' }
Write-Host 'Note: setx affects new processes. To use in current session, run: $env:AWS_BEARER_TOKEN_BEDROCK = "<token>"; $env:AWS_REGION = "<region>"'
