#!/usr/bin/env sh
# Tải Il2CppDumper bản Linux (net6, chạy bằng dotnet) vào dumper/Il2CppDumper-net6.
# Cần có .NET runtime 6+ (khuyên dùng 8.0, kèm DOTNET_ROLL_FORWARD=Major).
set -eu
VERSION="${IL2CPPDUMPER_VERSION:-v6.7.46}"
SHA256="db9bbbc538e33abfb057c7757ae5d6c1f16a05fdc0d13af8a5a67ea31faaba0c"
DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp)"
curl -sSL -o "$TMP" "https://github.com/Perfare/Il2CppDumper/releases/download/${VERSION}/Il2CppDumper-net6-${VERSION}.zip"
if [ "$VERSION" = "v6.7.46" ]; then echo "$SHA256  $TMP" | sha256sum -c -; fi
rm -rf "$DIR/Il2CppDumper-net6"
unzip -q "$TMP" -d "$DIR/Il2CppDumper-net6"
rm -f "$TMP"
cp "$DIR/config.json" "$DIR/Il2CppDumper-net6/config.json"
echo "OK: $DIR/Il2CppDumper-net6/Il2CppDumper.dll"
