#!/usr/bin/env sh
# Install PowerShell using a binary archive.
# This provides several benefits:
# * Pinning to a specific version.
# * Multiple architectures.
# * Side-by-side installation.

set -eu

version="$1"

arch="$(uname -i)"

if [ "${arch}" = "x86_64" ]; then
  arch="x64"
elif [ "${arch}" = "aarch64" ]; then
  arch="arm64"
else
  echo "unknown arch: ${arch}"
  exit 1
fi

major_version="$(echo "${version}" | cut -f 1 -d .)"
minor_version="$(echo "${version}" | cut -f 2 -d .)"
install_dir="/opt/microsoft/powershell/${major_version}.${minor_version}"
tmp_file="/tmp/powershell-${major_version}.${minor_version}.tgz"
url="https://github.com/PowerShell/PowerShell/releases/download/v${version}/powershell-${version}-linux-${arch}.tar.gz"

echo "Download PowerShell: ${url}"
curl -sL "${url}" > "${tmp_file}"
mkdir -p "${install_dir}"
tar zxf "${tmp_file}" --no-same-owner --no-same-permissions -C "${install_dir}"
rm "${tmp_file}"
find "${install_dir}" -type f -exec chmod -x "{}" ";"
chmod +x "${install_dir}/pwsh"
ln -s "${install_dir}/pwsh" "/usr/bin/pwsh${major_version}.${minor_version}"
ln -sf "${install_dir}/pwsh" /usr/bin/pwsh
pwsh --version
rm -rf /tmp/.dotnet
