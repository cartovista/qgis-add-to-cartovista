param(
    # Path where the output folder should be created
    [Parameter(Mandatory=$true)]
    [string]$DestinationParentFolder,

    # Whether the output folder should be zipped afterward
    [switch]$Zip,
    # Whether to use env_production or env_development's constants and swagger_client
    [switch]$Prod
)

$Destination = Join-Path ($DestinationParentFolder) ("add_to_cartovista")

# Determine script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Source directory (one level above script)
$SourceDir = Resolve-Path (Join-Path $ScriptDir "..")

# Hardcoded files/folders to copy (relative to $SourceDir)
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

# Resolve absolute destination path
if (Test-Path $Destination) {
    Write-Host "Existing output folder found. Removing: $Destination"
    Remove-Item -Recurse -Force $Destination
}


New-Item -ItemType Directory -Path $Destination -Force | Out-Null

$OutputDir = Resolve-Path $Destination

Write-Host "Source:      $SourceDir"
Write-Host "Destination: $OutputDir"
Write-Host ""

foreach ($item in $ItemsToCopy) {
    $SourcePath = Join-Path $SourceDir $item
    $DestPath   = Join-Path $OutputDir $item

    if (Test-Path $SourcePath) {
        Write-Host "Copying $item..."

        # Ensure directory structure exists
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

if ($Prod) {
    $env_folder = "env_production"
} else {
    $env_folder = "env_development"
}

foreach ($item in $EnvDependantItemsToCopy) {
    $SourcePath = Join-Path $SourceDir (Join-Path $env_folder $item)
    $DestPath   = Join-Path $OutputDir $item

    if (Test-Path $SourcePath) {
        Write-Host "Copying $item..."

        # Ensure directory structure exists
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
    Write-Host ""
    Write-Host "Zipping output folder..."

    $Parent = Split-Path $OutputDir -Parent
    $FolderName = Split-Path $OutputDir -Leaf
    $ZipPath = Join-Path $Parent "$FolderName.zip"

    if (Test-Path $ZipPath) {
        Write-Host "Existing zip found. Removing: $ZipPath"
        Remove-Item -Force $ZipPath
    }

    Compress-Archive -Path $OutputDir -DestinationPath $ZipPath -Force

    Write-Host "Created zip: $ZipPath"

    # Remove original unzipped folder
    Write-Host "Removing unzipped folder: $OutputDir"
    Remove-Item -Recurse -Force $OutputDir
}

Write-Host ""
Write-Host "Done."
