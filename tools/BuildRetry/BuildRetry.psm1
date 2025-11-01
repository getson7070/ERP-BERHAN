function Invoke-DockerBuildResilient {
  param([int]$Retries = 3)
  Write-Host "==> Resilient build: retries=$Retries" -ForegroundColor Cyan

  function _doBuild([string]$why){
    Write-Host "---- build attempt ($why) ----" -ForegroundColor DarkCyan
    docker compose build --no-cache
    return $LASTEXITCODE
  }

  for ($i=1; $i -le $Retries; $i++){
    if (_doBuild "normal try $i" -eq 0) { return }
    Start-Sleep -Seconds ([int][Math]::Min(20, 3 * $i))
  }

  if ($env:DOCKER_REGISTRY_MIRROR) {
    Write-Host "Using registry mirror: $env:DOCKER_REGISTRY_MIRROR" -ForegroundColor Yellow
    $env:DOCKER_BUILDKIT = "1"
    $env:BUILDKIT_REGISTRY_MIRRORS = $env:DOCKER_REGISTRY_MIRROR
    if (_doBuild "with mirror" -eq 0) { return }
  }

  $dockerfilePath = "dockerfile"
  if (Test-Path $dockerfilePath) {
    $txt = Get-Content $dockerfilePath -Raw
    if ($txt -match '#\s*syntax=docker/dockerfile:1\.7') {
      Write-Host "Pinning '# syntax=...' to 1.6 as a transient workaround..." -ForegroundColor Yellow
      $txt = $txt -replace '#\s*syntax=docker/dockerfile:1\.7', '# syntax=docker/dockerfile:1.6'
      Set-Content $dockerfilePath $txt -Encoding utf8
      try {
        if (_doBuild "pinned syntax 1.6" -eq 0) { return }
      } finally {
        $txt = (Get-Content $dockerfilePath -Raw) -replace '#\s*syntax=docker/dockerfile:1\.6', '# syntax=docker/dockerfile:1.7'
        Set-Content $dockerfilePath $txt -Encoding utf8
      }
    }
  }

  throw "All resilient build attempts failed. Check access to registry-1.docker.io or proxy."
}
Export-ModuleMember -Function Invoke-DockerBuildResilient
