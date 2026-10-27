param([switch]$Persist)

# Dot-source before project commands. No downloads, migration, deletion or secrets.
$storageProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ($storageProjectRoot -ne 'E:\projects\browser-agent-lab') {
    throw 'This storage policy is scoped to E:\projects\browser-agent-lab.'
}
$storageDirectories = [ordered]@{
    OLLAMA_MODELS = 'E:\AI\OllamaModels'
    UV_CACHE_DIR = 'E:\AI\Caches\uv'
    UV_PYTHON_INSTALL_DIR = 'E:\AI\Python'
    UV_PYTHON_CACHE_DIR = 'E:\AI\Downloads\uv-python'
    UV_PYTHON_BIN_DIR = 'E:\AI\Caches\bin'
    UV_TOOL_DIR = 'E:\AI\Caches\uv-tools'
    UV_TOOL_BIN_DIR = 'E:\AI\Caches\bin'
    UV_INSTALL_DIR = 'E:\AI\Caches\bin'
    NPM_CONFIG_CACHE = 'E:\AI\Caches\npm'
    NPM_CONFIG_PREFIX = 'E:\AI\Caches\npm-global'
    PIP_CACHE_DIR = 'E:\AI\Caches\pip'
    PLAYWRIGHT_BROWSERS_PATH = 'E:\AI\Caches\ms-playwright'
    BROWSER_USE_CONFIG_DIR = 'E:\AI\Caches\browser-use'
    XDG_CACHE_HOME = 'E:\AI\Caches'
    HF_HOME = 'E:\AI\Caches\huggingface'
    TORCH_HOME = 'E:\AI\Caches\torch'
    CUDA_CACHE_PATH = 'E:\AI\Caches\cuda'
    TEMP = 'E:\AI\Downloads\Temp'
    TMP = 'E:\AI\Downloads\Temp'
    TMPDIR = 'E:\AI\Downloads\Temp'
}
foreach ($storageEntry in $storageDirectories.GetEnumerator()) {
    if ([IO.Path]::GetPathRoot($storageEntry.Value) -ne 'E:\') {
        throw "Non-E: destination rejected: $($storageEntry.Key)"
    }
    New-Item -ItemType Directory -Path $storageEntry.Value -Force | Out-Null
    [Environment]::SetEnvironmentVariable($storageEntry.Key, $storageEntry.Value, 'Process')
    if ($Persist -and [Environment]::GetEnvironmentVariable($storageEntry.Key, 'User') -ne $storageEntry.Value) {
        [Environment]::SetEnvironmentVariable($storageEntry.Key, $storageEntry.Value, 'User')
    }
}
New-Item -ItemType Directory -Path 'E:\AI\Downloads' -Force | Out-Null
$env:PLAYWRIGHT_SKIP_BROWSER_GC = '1'
if ($Persist -and [Environment]::GetEnvironmentVariable('PLAYWRIGHT_SKIP_BROWSER_GC', 'User') -ne '1') {
    [Environment]::SetEnvironmentVariable('PLAYWRIGHT_SKIP_BROWSER_GC', '1', 'User')
}
# Keep project-specific interpreter selection scoped to this shell, not all projects.
$env:UV_PROJECT_ENVIRONMENT = Join-Path $storageProjectRoot '.venv'
$storageManagedPython = 'E:\AI\Python\cpython-3.11-windows-x86_64-none'
if (Test-Path -LiteralPath (Join-Path $storageManagedPython 'python.exe')) {
    $env:UV_PYTHON = Join-Path $storageManagedPython 'python.exe'
}
$storageToolPaths = @(
    (Join-Path $storageProjectRoot '.venv\Scripts'),
    $storageManagedPython,
    (Join-Path $storageProjectRoot '.tools\bin'),
    (Join-Path $storageProjectRoot '.tools\nodejs'),
    (Join-Path $storageProjectRoot '.tools\node_modules\node\bin'),
    (Join-Path $storageProjectRoot '.tools\github-cli\bin'),
    'E:\AI\Ollama'
) | Where-Object { Test-Path -LiteralPath $_ }
$env:PATH = (($storageToolPaths + @($env:PATH)) -join ';')
