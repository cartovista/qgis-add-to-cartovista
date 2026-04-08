param(
    # Paths where the output folder should be created
    [Parameter(Mandatory=$true)]
    [string[]]$DestinationParentFolders,

    [switch]$Zip,
    [switch]$Prod
)

# Determine script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Resolve-Path (Join-Path $ScriptDir "..")

$ItemsToCopy = @(
    "metadata.txt",
    "assets",
    "authorization",
    "core",
    "dialogs",
    "plugin.py",
    "LICENSE",
    "README.md",
    "__init__.py"
)

$EnvDependantItemsToCopy = @(
    "constants.py",
    "swagger_client"
)

if ($Prod) {
    $env_folder = "env_production"
} else {
    $env_folder = "env_development"
}

foreach ($DestinationParentFolder in $DestinationParentFolders) {

    if (-not (Test-Path $DestinationParentFolder)) {
        Write-Warning "Destination does not exist, skipping: $DestinationParentFolder"
        continue
    }

    $Destination = Join-Path $DestinationParentFolder "add_to_cartovista"

    if (Test-Path $Destination) {
        Write-Host "Removing existing folder: $Destination"
        Remove-Item -Recurse -Force $Destination
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $OutputDir = Resolve-Path $Destination

    Write-Host ""
    Write-Host "Destination: $OutputDir"

    foreach ($item in $ItemsToCopy) {
        $SourcePath = Join-Path $SourceDir $item
        $DestPath   = Join-Path $OutputDir $item

        if (Test-Path $SourcePath) {
            $DestDir = Split-Path -Parent $DestPath
            if (-not (Test-Path $DestDir)) {
                New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
            }

            Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force
        }
        else {
            Write-Warning "Item not found: $item"
        }
    }

    foreach ($item in $EnvDependantItemsToCopy) {
        $SourcePath = Join-Path $SourceDir (Join-Path $env_folder $item)
        $DestPath   = Join-Path $OutputDir $item

        if (Test-Path $SourcePath) {
            $DestDir = Split-Path -Parent $DestPath
            if (-not (Test-Path $DestDir)) {
                New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
            }

            Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force
        }
        else {
            Write-Warning "Item not found: $item"
        }
    }

    if ($Zip) {
        $Parent = Split-Path $OutputDir -Parent
        $FolderName = Split-Path $OutputDir -Leaf
        $ZipPath = Join-Path $Parent "$FolderName.zip"

        if (Test-Path $ZipPath) {
            Remove-Item -Force $ZipPath
        }

        Compress-Archive -Path $OutputDir -DestinationPath $ZipPath -Force
        Remove-Item -Recurse -Force $OutputDir

        Write-Host "Created zip: $ZipPath"
    }
}

Write-Host ""
Write-Host "Done."
