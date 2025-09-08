$ErrorActionPreference = "Stop"

# Always run from this script's directory so relative -f paths work
Set-Location -Path $PSScriptRoot

# Ensure locally built images are loaded into the engine by default
if (-not $env:DOCKER_BUILDKIT) { $env:DOCKER_BUILDKIT = "0" }

# Build arguments (UIDs are mainly for Linux; on Windows default to 1000/2001 unless overridden)
$BOT_UID = if ($env:BOT_UID) { $env:BOT_UID } else { "2001" }
$STARCRAFT_UID = if ($env:STARCRAFT_UID) { $env:STARCRAFT_UID } else { "1000" }
$commonArgs = @("--build-arg", "BOT_UID=$BOT_UID", "--build-arg", "STARCRAFT_UID=$STARCRAFT_UID")

# Choose builder: default classic docker build; allow USE_BUILDX=1
$useBuildx = ($env:USE_BUILDX -eq '1')
$hasBuildx = $false
try { docker buildx version *>$null; $hasBuildx = $true } catch { $hasBuildx = $false }

$buildCmd = @("docker", "build")
$loadArgs = @()  # Only used with buildx
if ($useBuildx -and $hasBuildx) {
    # Inspect driver to guide the user
    $inspect = docker buildx inspect 2>$null
    $driver = ($inspect | Select-String -Pattern '^Driver:\s*(.+)$').Matches.Groups[1].Value
    if (-not $driver) { $driver = "unknown" }
    Write-Host "INFO: USE_BUILDX=1 detected. buildx driver: $driver" -ForegroundColor Yellow
    if ($driver -ne "docker") {
        Write-Warning @"
Your buildx builder is not using the 'docker' driver (likely 'docker-container').
With the container driver, builds run in an isolated environment and local images
(e.g., 'starcraft:wine') are NOT visible as FROM bases. You may see errors like:
  "pull access denied, repository does not exist or may require authorization"

Fix options:
  1) Recommended: use the classic builder (local images are visible):
       setx USE_BUILDX ""   # or `$env:USE_BUILDX=""` for current session
       .\build_images.ps1

  2) Or create/switch to a buildx builder that uses the docker driver:
       docker buildx create --use --driver docker --name scbw-docker
       # then re-run:
       setx USE_BUILDX 1     # or `$env:USE_BUILDX="1"` for current session
       .\build_images.ps1
"@
    }
    $buildCmd = @("docker", "buildx", "build")
    $loadArgs = @("--load")
} elseif ($useBuildx -and -not $hasBuildx) {
    Write-Host "INFO: USE_BUILDX=1 requested but docker buildx not found; falling back to classic docker build." -ForegroundColor Yellow
}

function Invoke-Build {
    param(
        [string]$Dockerfile,
        [string]$Tag,
        [string]$Context = "."
    )
    & $buildCmd @commonArgs @loadArgs -f $Dockerfile -t $Tag $Context
    if ($LASTEXITCODE -ne 0) { throw "Failed to build $Tag (dockerfile: $Dockerfile)" }
}

Invoke-Build -Dockerfile "dockerfiles/wine.dockerfile" -Tag "starcraft:wine"
Invoke-Build -Dockerfile "dockerfiles/bwapi.dockerfile" -Tag "starcraft:bwapi"
Invoke-Build -Dockerfile "dockerfiles/play.dockerfile" -Tag "starcraft:play"
Invoke-Build -Dockerfile "dockerfiles/java.dockerfile" -Tag "starcraft:java"

Push-Location ..\scbw\local_docker
if (!(Test-Path starcraft.zip)) {
    Invoke-WebRequest 'http://files.theabyss.ru/sc/starcraft.zip' -OutFile starcraft.zip
}
Invoke-Build -Dockerfile "game.dockerfile" -Tag "starcraft:game" -Context "."
Pop-Location

Invoke-Build -Dockerfile "dockerfiles/dbg.dockerfile" -Tag "starcraft:dbg"
