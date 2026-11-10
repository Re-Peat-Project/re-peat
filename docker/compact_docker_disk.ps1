<#
Free disk space taken by Docker Desktop (WSL 2 backend): prune what Docker no longer needs, then compact its virtual disk
(docker_data.vhdx), which never shrinks by itself.

Run from an administrator PowerShell (the compaction needs it); Docker Desktop must be running for the prune steps:
    powershell -ExecutionPolicy Bypass -File compact_docker_disk.ps1            # asks before every step
    powershell -ExecutionPolicy Bypass -File compact_docker_disk.ps1 -Yes       # no questions
    ... -AllUnusedImages      also remove every image no container uses (not only the untagged ones); rebuild repeat-chain after
    ... -SkipPrune            only compact (Docker may already be stopped)
    ... -NoRestart            leave Docker Desktop stopped afterwards

Steps:
  1. docker builder prune -a     all build cache (failed and finished builds); images and containers stay
  2. docker image prune          untagged (dangling) images; with -AllUnusedImages: docker image prune -a
  3. stop Docker Desktop and WSL (wsl --shutdown)
  4. compact docker_data.vhdx    Optimize-VHD when the Hyper-V module is installed, otherwise diskpart "compact vdisk"
  5. start Docker Desktop again
Nothing outside Docker is touched. Containers, volumes and tagged images that are in use are kept.
#>
param(
    [switch]$Yes,
    [switch]$AllUnusedImages,
    [switch]$SkipPrune,
    [switch]$NoRestart,
    [string]$Vhdx = (Join-Path $env:LOCALAPPDATA "Docker\wsl\disk\docker_data.vhdx"),
    [string]$DockerExe = (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe")
)
$ErrorActionPreference = "Stop"

function Confirm-Step([string]$what) {
    if ($Yes) { return $true }
    $a = Read-Host "$what  [y/N]"
    return $a -match '^(y|yes)$'
}

function Get-FreeGB { [math]::Round((Get-PSDrive C).Free / 1GB, 1) }

function Get-VhdxGB {
    if (Test-Path $Vhdx) { [math]::Round((Get-Item $Vhdx).Length / 1GB, 1) } else { $null }
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Not an administrator PowerShell: the prune steps run, the compaction (step 4) will be skipped."
}

$free0 = Get-FreeGB
$vhd0 = Get-VhdxGB
Write-Host "C: free $free0 GB; docker_data.vhdx $vhd0 GB ($Vhdx)"

# 1-2. prune (needs the Docker engine)
if (-not $SkipPrune) {
    docker info --format "{{.ServerVersion}}" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker engine not reachable: start Docker Desktop first, or run with -SkipPrune to only compact."
    }
    Write-Host "`nWhat Docker holds now:"
    docker system df
    if (Confirm-Step "1. Remove ALL build cache (docker builder prune -a)?") {
        docker builder prune -a -f
    }
    if ($AllUnusedImages) {
        Write-Host "`nImages no container uses (these would go):"
        docker images --filter "dangling=false" --format "  {{.Repository}}:{{.Tag}}  {{.Size}}"
        if (Confirm-Step "2. Remove every image no container uses (docker image prune -a)?") { docker image prune -a -f }
    } elseif (Confirm-Step "2. Remove untagged (dangling) images (docker image prune)?") {
        docker image prune -f
    }
    Write-Host "`nAfter pruning:"
    docker system df
}

# 3-4. stop Docker and WSL, compact the virtual disk
if (-not $isAdmin) {
    Write-Warning "Skipping the compaction: rerun from an administrator PowerShell with -SkipPrune."
} elseif (-not (Test-Path $Vhdx)) {
    Write-Warning "No virtual disk at $Vhdx; nothing to compact (pass -Vhdx <path>)."
} elseif (Confirm-Step "3-4. Stop Docker Desktop and WSL, then compact $Vhdx?") {
    Get-Process "Docker Desktop", "com.docker.backend", "com.docker.build" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 5
    wsl --shutdown
    Start-Sleep -Seconds 5
    if (Get-Command Optimize-VHD -ErrorAction SilentlyContinue) {
        Write-Host "Compacting with Optimize-VHD (this can take several minutes)..."
        Optimize-VHD -Path $Vhdx -Mode Full
    } else {
        Write-Host "Compacting with diskpart (this can take several minutes)..."
        $script = Join-Path $env:TEMP "compact_docker_vhdx.txt"
        @(
            "select vdisk file=`"$Vhdx`"",
            "attach vdisk readonly",
            "compact vdisk",
            "detach vdisk"
        ) | Set-Content -Path $script -Encoding ASCII
        diskpart /s $script
        Remove-Item $script -ErrorAction SilentlyContinue
    }
}

# 5. start Docker Desktop again
if (-not $NoRestart -and (Test-Path $DockerExe) -and -not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Start-Process $DockerExe
    Write-Host "Docker Desktop started again."
}

$free1 = Get-FreeGB
$vhd1 = Get-VhdxGB
Write-Host "`nC: free $free0 -> $free1 GB; docker_data.vhdx $vhd0 -> $vhd1 GB"
