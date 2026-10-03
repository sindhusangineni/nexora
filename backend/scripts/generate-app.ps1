[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = "The name of the backend feature module to generate.")]
    [ValidateNotNullOrEmpty()]
    [string]$AppName
)

# 1. Validate AppName: lowercase, letters/numbers/underscores only, cannot start with a number
if ($AppName -notmatch '^[a-z][a-z0-9_]*$') {
    Write-Error "Invalid AppName '$AppName'. It must be lowercase, start with a letter, and contain only letters, numbers, and underscores."
    exit 1
}

# 2. Reject Python and Django reserved words
$ReservedNames = @(
    # Python keywords
    "and", "as", "assert", "async", "await", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from",
    "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
    "or", "pass", "raise", "return", "try", "while", "with", "yield",
    "true", "false", "none",
    # Python standard / built-in modules
    "test", "tests", "site", "math", "os", "sys", "json", "io", "re", "datetime", "types",
    # Django apps and core names
    "django", "admin", "auth", "contenttypes", "sessions", "messages",
    "staticfiles", "config", "apps", "manage", "settings", "urls", "wsgi", "asgi", "core", "shared"
)

if ($ReservedNames -contains $AppName.ToLower()) {
    Write-Error "AppName '$AppName' is a reserved Python or Django name and cannot be used."
    exit 1
}

# 3. Determine paths relative to this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
$AppsDir = Join-Path $BackendDir "apps"
$TargetAppDir = Join-Path $AppsDir $AppName

# 4. Reject existing app directory
if (Test-Path $TargetAppDir) {
    Write-Error "App directory already exists: $TargetAppDir"
    exit 1
}

# 5. Ensure parent apps/ directory exists with __init__.py
if (-not (Test-Path $AppsDir)) {
    New-Item -ItemType Directory -Path $AppsDir -Force | Out-Null
    Write-Host "Created directory: apps/" -ForegroundColor Cyan
}

$AppsInit = Join-Path $AppsDir "__init__.py"
if (-not (Test-Path $AppsInit)) {
    New-Item -ItemType File -Path $AppsInit -Force | Out-Null
    Write-Host "Created file:      apps/__init__.py" -ForegroundColor Cyan
}

Write-Host "Generating feature module: apps.$AppName" -ForegroundColor Cyan
Write-Host "Location: $TargetAppDir`n"

# 6. Create app root and __init__.py
New-Item -ItemType Directory -Path $TargetAppDir -Force | Out-Null
Write-Host "Created directory: apps/$AppName/"

$AppInit = Join-Path $TargetAppDir "__init__.py"
New-Item -ItemType File -Path $AppInit -Force | Out-Null
Write-Host "Created file:      apps/$AppName/__init__.py"

# 7. Create subdirectories with __init__.py
$Subdirectories = @(
    "migrations",
    "models",
    "managers",
    "serializers",
    "services",
    "selectors",
    "permissions",
    "validators",
    "views",
    "urls",
    "tests"
)

foreach ($SubDir in $Subdirectories) {
    $DirPath = Join-Path $TargetAppDir $SubDir
    New-Item -ItemType Directory -Path $DirPath -Force | Out-Null
    Write-Host "Created directory: apps/$AppName/$SubDir/"

    $InitPath = Join-Path $DirPath "__init__.py"
    New-Item -ItemType File -Path $InitPath -Force | Out-Null
    Write-Host "Created file:      apps/$AppName/$SubDir/__init__.py"
}

# 8. Create apps.py with AppConfig
$PascalCaseName = ($AppName.Split('_') | ForEach-Object {
    if ($_.Length -gt 1) {
        $_.Substring(0, 1).ToUpper() + $_.Substring(1)
    } else {
        $_.ToUpper()
    }
}) -join ''

$AppsPyContent = @"
from django.apps import AppConfig


class ${PascalCaseName}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.$AppName"
"@

$AppsPyPath = Join-Path $TargetAppDir "apps.py"
Set-Content -Path $AppsPyPath -Value $AppsPyContent
Write-Host "Created file:      apps/$AppName/apps.py"

# 9. Create admin.py
$AdminPyContent = @"
from django.contrib import admin

# Register your models here.
"@

$AdminPyPath = Join-Path $TargetAppDir "admin.py"
Set-Content -Path $AdminPyPath -Value $AdminPyContent
Write-Host "Created file:      apps/$AppName/admin.py"

Write-Host "`nFeature module 'apps.$AppName' created successfully." -ForegroundColor Green
