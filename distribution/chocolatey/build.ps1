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
$zipSha = 'f3013cd6722bdcd3c2df6a58acd4e3801af2b34e877e132a1242dc3816021886'
$exeSha = '03f673307c3a399c30fecbcaa1047b00ed755d4d29b62dda73c559b5d688207d'
$sourceSha = '642f1cd4abcf16c2100eb8fdc2a84691a2af3d78549af4efce7398c2c6a78e17'

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
Build commit: 897dd50cdf27cbde54d408bf65e1ca4622035d42
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
