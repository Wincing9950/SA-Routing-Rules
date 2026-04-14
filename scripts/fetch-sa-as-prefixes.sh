#!/bin/bash
# fetch-sa-as-prefixes.sh
# Fetches all BGP-announced IP prefixes from major Saudi Arabian ASes
# via the RIPE Stat API (https://stat.ripe.net/api/v2/).
# Output: sa-ips/sa-bgp-prefixes.txt

set -euo pipefail

echo "==> Fetching BGP-announced SA AS prefixes from RIPE Stat API..."

mkdir -p sa-ips

# Major Saudi ASes:
# AS39386 - Mobily (Etihad Etisalat) primary
# AS35819 - Mobily (alternate)
# AS8895  - Zain Saudi Arabia
# AS25019 - STC subsidiary / Etihad Etisalat
# AS28620 - STC (Saudi Telecom Company) primary
# AS47357 - STC (alternate)
# AS39648 - STC (alternate)
# AS47794 - Integrated Telecom (Salam)
# AS198515 - GO Telecom
# AS21050  - Bayanat Al-Oula
SA_ASES="39386 35819 8895 25019 28620 47357 39648 47794 198515 21050"

TMP_FILE="$(mktemp /tmp/sa-bgp-XXXXXX.txt)"
trap "rm -f $TMP_FILE" EXIT

for asn in $SA_ASES; do
  echo "  -> Querying AS${asn}..."
  RESP=$(curl -s --max-time 15 \
    "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS${asn}" 2>/dev/null || echo '{}')

  echo "$RESP" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    prefixes = data.get('data', {}).get('prefixes', [])
    for p in prefixes:
        print(p.get('prefix', ''))
except Exception:
    pass
" >> "$TMP_FILE"

  sleep 0.3
done

# Sort, deduplicate, remove empty lines
{ grep -v '^$' "$TMP_FILE" || true; } | LC_ALL=C sort -u > sa-ips/sa-bgp-prefixes.txt

IPV4_COUNT=$(grep -c '\.' sa-ips/sa-bgp-prefixes.txt 2>/dev/null) || IPV4_COUNT=0
IPV6_COUNT=$(grep -c ':' sa-ips/sa-bgp-prefixes.txt 2>/dev/null) || IPV6_COUNT=0
echo "  -> BGP prefixes: ${IPV4_COUNT} IPv4, ${IPV6_COUNT} IPv6"
echo "==> Done fetching BGP prefixes"
