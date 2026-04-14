#!/bin/bash
# reverse-dns-sweep.sh
# Performs a PTR (reverse DNS) sweep on Saudi Arabian IPv4 ranges.
# Requires: massdns (https://github.com/blechschmidt/massdns)
#           python3 scripts/cidr-to-sample-ips.py
# Output: sa-ips/sa-ptr-domains.txt
#
# Strategy: one IP per /24 subnet reduces queries to ~5K for full SA space.
# Run weekly as part of the build pipeline.

set -euo pipefail

CIDR_FILE="${1:-sa-ips/sa-ipv4-ripe.txt}"

mkdir -p sa-ips

if ! command -v massdns &>/dev/null; then
  echo "  WARNING: massdns not installed, skipping reverse DNS sweep."
  echo "  Install from: https://github.com/blechschmidt/massdns"
  touch sa-ips/sa-ptr-domains.txt
  exit 0
fi

if [ ! -f "$CIDR_FILE" ]; then
  echo "  WARNING: CIDR file not found: $CIDR_FILE"
  touch sa-ips/sa-ptr-domains.txt
  exit 0
fi

echo "==> Reverse DNS sweep on Saudi IP space..."

mkdir -p sa-ips

echo "  -> Generating IP sample from ${CIDR_FILE}..."
python3 ./scripts/cidr-to-sample-ips.py "${CIDR_FILE}" > /tmp/sa-sample-ips.txt
IP_COUNT=$(wc -l < /tmp/sa-sample-ips.txt)
echo "  -> Sampled ${IP_COUNT} IPs (one per /24)"

# Convert to in-addr.arpa PTR query format
awk -F. '{print $4"."$3"."$2"."$1".in-addr.arpa"}' /tmp/sa-sample-ips.txt \
  > /tmp/sa-ptr-queries.txt

echo -e "1.1.1.1\n8.8.8.8\n9.9.9.9" > /tmp/resolvers.txt

echo "  -> Running massdns on ${IP_COUNT} queries..."
touch sa-ips/sa-ptr-domains.txt
massdns -r /tmp/resolvers.txt \
        -t PTR \
        --retry REFUSED \
        -o S \
        /tmp/sa-ptr-queries.txt 2>/dev/null \
  | { grep -v 'SERVFAIL\|NXDOMAIN\|NOERROR.*0 answer' || true; } \
  | awk '/IN PTR/ {gsub(/\.$/, "", $NF); print $NF}' \
  | { grep -v '^$' || true; } \
  | { grep '\.' || true; } \
  | LC_ALL=C sort -u > sa-ips/sa-ptr-domains.txt || true

PTR_COUNT=$(wc -l < sa-ips/sa-ptr-domains.txt) || PTR_COUNT=0
echo "  -> Discovered ${PTR_COUNT} PTR hostnames"
echo "==> Reverse DNS sweep complete"
