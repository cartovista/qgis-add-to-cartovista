param(
    # Whether to use env_production instead of env_development
    [switch]$Prod
)
Push-Location
Set-Location -Path $PSScriptRoot
./create_plugin_folder.ps1 C:\Users\$Env:UserName\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins -Prod:$Prod
Pop-Location