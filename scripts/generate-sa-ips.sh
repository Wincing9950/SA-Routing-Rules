#!/bin/bash
# generate-sa-ips.sh
# Generates Saudi Arabia IP address ranges from RIPE NCC delegated statistics
# and other authoritative sources

set -euo pipefail

echo "==> Generating Saudi Arabia IP ranges..."

mkdir -p sa-ips

# --- Source 1: RIPE NCC Delegated Statistics ---
echo "  -> Fetching RIPE NCC delegated stats..."
curl -sSL "https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-extended-latest" -o ripencc-delegated.txt

# Extract Saudi Arabia IPv4 allocations and convert to CIDR
echo "  -> Extracting SA IPv4 ranges..."
python3 scripts/ripe-to-cidr.py ripencc-delegated.txt SA ipv4 > sa-ips/sa-ipv4-ripe.txt

# Extract Saudi Arabia IPv6 allocations
echo "  -> Extracting SA IPv6 ranges..."
python3 scripts/ripe-to-cidr.py ripencc-delegated.txt SA ipv6 > sa-ips/sa-ipv6-ripe.txt

# Combine IPv4 and IPv6
cat sa-ips/sa-ipv4-ripe.txt sa-ips/sa-ipv6-ripe.txt | LC_ALL=C sort -u > sa-ips/sa-ripe.txt

echo "  -> Generated $(wc -l < sa-ips/sa-ipv4-ripe.txt) IPv4 CIDR blocks"
echo "  -> Generated $(wc -l < sa-ips/sa-ipv6-ripe.txt) IPv6 CIDR blocks"

# --- Source 2: Additional Saudi ISP/CDN IPs (manually maintained) ---
echo "  -> Loading additional Saudi ISP IPs..."
if [ -f ./data/sa-extra-ips.txt ]; then
  cat ./data/sa-extra-ips.txt >> sa-ips/sa-ripe.txt
fi

# Final sort and dedup
LC_ALL=C sort -u sa-ips/sa-ripe.txt > sa-ips/sa-all.txt

echo "  -> Total: $(wc -l < sa-ips/sa-all.txt) unique CIDR blocks"
echo "==> Done generating Saudi Arabia IP ranges"

# Cleanup
rm -f ripencc-delegated.txt
