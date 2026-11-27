param(
    [Parameter(Mandatory)]
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$id = 'qrcode-barcode-scanner'
[xml]$spec = Get-Content -LiteralPath (Join-Path $PSScriptRoot "$id.nuspec") -Raw
$version = $spec.package.metadata.version
$asset = "$id-cli-$version-x86_64-pc-windows-msvc"
$release = "https://github.com/qrcode-ai-com/$id/releases/download/v$version"
$zipSha = 'e62c1c0e4846f595d7ca71b627c246d458347cd51a2b26196789bc469a3af83a'
$exeSha = '4545fc71ab7acef5b4e2d7b8040cae6ef9d57490aaa3df6e0cc5cb800f4bb4de'
$sourceSha = 'ceed71c46c7a8b908d53ad79a7b7fb67e8bc04c6e4b30e61dbfd9bff6db402f8'

$output = (New-Item -ItemType Directory -Path $OutputDirectory -Force).FullName
$package = Join-Path $output "$id.$version.nupkg"
if (Test-Path -LiteralPath $package) { throw "Package already exists: $package" }

$work = (New-TemporaryFile).FullName
Remove-Item -LiteralPath $work
New-Item -ItemType Directory -Path $work | Out-Null
try {
    $zip = Join-Path $work "$asset.zip"
    Invoke-WebRequest "$release/$asset.zip" -OutFile $zip
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ine $zipSha) {
        throw 'Windows release ZIP SHA-256 mismatch.'
    }

    $extracted = Join-Path $work 'release'
    Expand-Archive -LiteralPath $zip -DestinationPath $extracted
    $upstream = Join-Path $extracted $asset
    if ((Get-FileHash -LiteralPath (Join-Path $upstream 'qrscan.exe') -Algorithm SHA256).Hash -ine $exeSha) {
        throw 'Windows release executable SHA-256 mismatch.'
    }

    $stage = Join-Path $work 'package'
    $tools = Join-Path $stage 'tools'
    New-Item -ItemType Directory -Path $tools -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "$id.nuspec") -Destination $stage
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'tools/chocolateyinstall.ps1') -Destination $tools
    foreach ($file in Get-ChildItem -LiteralPath $upstream -File) {
        Copy-Item -LiteralPath $file.FullName -Destination $tools
    }
    Copy-Item -LiteralPath (Join-Path $tools 'LICENSE') -Destination (Join-Path $tools 'LICENSE.txt')
    @"
Package verification

The embedded qrscan.exe comes from the official release for Windows x64.

Windows ZIP: $release/$asset.zip
ZIP SHA-256: $zipSha
qrscan.exe SHA-256: $exeSha

Verify the ZIP SHA-256, extract it, then compare the SHA-256 of both
qrscan.exe files with the executable hash above.

Corresponding source: $release/$id-cli-$version-source.tar.gz
Source archive SHA-256: $sourceSha
Build commit: d0fcf8a27410f5ee182aab6477624e3fc52c4aa5
See SOURCE.md and build-info.json for the build recipe and dependency sources.
"@ | Set-Content -LiteralPath (Join-Path $tools 'VERIFICATION.txt') -Encoding utf8

    & choco pack (Join-Path $stage "$id.nuspec") "--outputdirectory=$output" --no-progress | Out-Host

    # Compare the embedded payload, including all upstream notices, byte for byte.
    $packed = Join-Path $work 'packed'
    [System.IO.Compression.ZipFile]::ExtractToDirectory($package, $packed)
    $packedTools = Join-Path $packed 'tools'
    $stagedFiles = @(Get-ChildItem -LiteralPath $tools -File)
    if (@(Get-ChildItem -LiteralPath $packedTools -File).Count -ne $stagedFiles.Count) {
        throw 'Unexpected packaged tools contents.'
    }
    foreach ($file in $stagedFiles) {
        $expected = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        $actual = (Get-FileHash -LiteralPath (Join-Path $packedTools $file.Name) -Algorithm SHA256).Hash
        if ($actual -cne $expected) { throw "Packaged bytes changed: $($file.Name)" }
    }
    Get-Item -LiteralPath $package
}
finally {
    Remove-Item -LiteralPath $work -Recurse -Force
}
