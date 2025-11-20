param(
    # Whether to use env_production instead of env_development
    [switch]$Prod
)
Push-Location
Set-Location -Path $PSScriptRoot
./create_plugin_folder.ps1 $PSScriptRoot -Zip -Prod:$Prod
Pop-Location