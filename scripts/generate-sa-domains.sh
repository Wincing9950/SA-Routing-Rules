#!/bin/bash
# generate-sa-domains.sh
# Generates the Saudi Arabia domain list from multiple sources
# Sources:
#   1. Curated Saudi domains (data/sa-domains.txt)
#   2. Saudi government portals (data/sa-gov-domains.txt)
#   3. Saudi services and apps (data/sa-services-domains.txt)
#   4. Bank domains from karenyousefi/bank-domains
#   5. CrUX Top Lists (Chrome UX Report) - filtered for Saudi Arabia

set -euo pipefail

echo "==> Generating Saudi Arabia domain list..."

mkdir -p domains

# --- Source 1: Download bank domains for SA ---
echo "  -> Fetching Saudi bank domains..."
curl -sSL "https://raw.githubusercontent.com/karenyousefi/bank-domains/main/sa/list.txt" -o sa-banks.txt 2>/dev/null || echo "" > sa-banks.txt

# --- Source 2: Curated Saudi domains (maintained in this repo) ---
echo "  -> Loading curated Saudi domains..."
cat ./data/sa-domains.txt > sa-curated.txt 2>/dev/null || echo "" > sa-curated.txt

# --- Source 3: Saudi government domains (maintained in this repo) ---
echo "  -> Loading Saudi government domains..."
cat ./data/sa-gov-domains.txt > sa-gov.txt 2>/dev/null || echo "" > sa-gov.txt

# --- Source 4: Saudi services and apps domains ---
echo "  -> Loading Saudi services domains..."
cat ./data/sa-services-domains.txt > sa-services.txt 2>/dev/null || echo "" > sa-services.txt

# --- Source 5: CrUX Top Lists (pre-filtered) ---
echo "  -> Loading CrUX-filtered Saudi domains..."
if [ -f ./data/sa-crux-domains.txt ]; then
  cat ./data/sa-crux-domains.txt > sa-crux.txt
  echo "     Found $(grep -v '^#' sa-crux.txt | grep -v '^$' | wc -l) CrUX domains"
else
  echo "" > sa-crux.txt
  echo "     CrUX domains file not found, skipping"
fi

# --- Source 6: Try to fetch latest CrUX data from upstream ---
echo "  -> Checking for updated CrUX data..."
if command -v python3 &>/dev/null && [ -f ./scripts/filter_crux_sa_domains.py ]; then
  # Find the latest YYYYMM.csv.gz in the InternetHealthReport CrUX country repo
  CRUX_LATEST=$(curl -s --max-time 10 \
    "https://api.github.com/repos/InternetHealthReport/crux-top-lists-country/contents/data/country/sa" \
    | python3 -c "import json,sys; items=json.load(sys.stdin); print(sorted([i['name'] for i in items if i['name'].endswith('.csv.gz')])[-1])" 2>/dev/null || echo "")
  CRUX_URL=""
  if [ -n "$CRUX_LATEST" ]; then
    CRUX_URL="https://raw.githubusercontent.com/InternetHealthReport/crux-top-lists-country/main/data/country/sa/${CRUX_LATEST}"
  fi
  if [ -n "$CRUX_URL" ] && curl -sSL --fail "$CRUX_URL" -o /tmp/crux-sa-latest.csv.gz 2>/dev/null; then
    gunzip -f /tmp/crux-sa-latest.csv.gz 2>/dev/null || true
    if [ -f /tmp/crux-sa-latest.csv ] && [ -s /tmp/crux-sa-latest.csv ]; then
      echo "     Running CrUX filter pipeline..."
      DNS_FLAG=""
      if [ "${SKIP_DNS:-false}" = "false" ]; then
        DNS_FLAG="--resolve-dns --max-workers 200"
      fi
      if [ -f ./sa-ips/sa-all.txt ]; then
        python3 ./scripts/filter_crux_sa_domains.py /tmp/crux-sa-latest.csv \
          -i ./sa-ips/sa-all.txt \
          -o sa-crux-live.txt \
          $DNS_FLAG 2>/dev/null || true
      else
        python3 ./scripts/filter_crux_sa_domains.py /tmp/crux-sa-latest.csv \
          -o sa-crux-live.txt \
          $DNS_FLAG 2>/dev/null || true
      fi
      if [ -s sa-crux-live.txt ]; then
        cat sa-crux-live.txt >> sa-crux.txt
        echo "     Added live CrUX domains"
      fi
    fi
  else
    echo "     Could not fetch latest CrUX data, using cached version"
  fi
fi

# --- Source 7: Certificate Transparency (crt.sh) ---
echo "  -> Fetching Certificate Transparency domains..."
if [ -f ./scripts/fetch-ct-domains.py ]; then
  python3 ./scripts/fetch-ct-domains.py -o sa-ct.txt 2>/dev/null || true
  CT_COUNT=$(grep -v '^#' sa-ct.txt 2>/dev/null | grep -v '^$' | wc -l || echo 0)
  echo "     Found ${CT_COUNT} CT domains"
else
  touch sa-ct.txt
fi

# --- Source 8: Majestic Million ---
echo "  -> Filtering Majestic Million..."
if [ -f ./scripts/fetch-majestic-sa.py ]; then
  MAJESTIC_DNS_FLAG=""
  if [ "${SKIP_DNS:-false}" = "false" ] && [ -f ./sa-ips/sa-all.txt ]; then
    MAJESTIC_DNS_FLAG="--resolve-dns --ip-file ./sa-ips/sa-all.txt"
  fi
  python3 ./scripts/fetch-majestic-sa.py $MAJESTIC_DNS_FLAG -o sa-majestic.txt 2>/dev/null || true
  MAJ_COUNT=$(grep -v '^#' sa-majestic.txt 2>/dev/null | grep -v '^$' | wc -l || echo 0)
  echo "     Found ${MAJ_COUNT} Majestic SA domains"
else
  touch sa-majestic.txt
fi

# --- Source 9: Reverse DNS PTR hostnames ---
echo "  -> Loading PTR hostnames from reverse DNS sweep..."
if [ -f ./sa-ips/sa-ptr-domains.txt ]; then
  PTR_COUNT=$(wc -l < sa-ips/sa-ptr-domains.txt)
  echo "     Found ${PTR_COUNT} PTR domains"
  cat sa-ips/sa-ptr-domains.txt > sa-ptr.txt
else
  touch sa-ptr.txt
fi

# --- Combine all sources ---
echo "  -> Combining all domain sources..."
cat sa-banks.txt sa-curated.txt sa-gov.txt sa-services.txt \
    sa-crux.txt sa-ct.txt sa-majestic.txt sa-ptr.txt | \
  sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | \
  grep -v '^#' | \
  grep -v '^$' | \
  tr '[:upper:]' '[:lower:]' | \
  LC_ALL=C sort -u > sa-all-tmp.txt

# Add the .sa TLD itself and its IDN equivalent
{
  echo "sa"
  echo "xn--mgbaam7a8h"
  cat sa-all-tmp.txt
} | LC_ALL=C sort -u > domains/sa.txt

# Create category-specific lists
echo "  -> Creating category lists..."
grep -v '^#' sa-gov.txt 2>/dev/null | grep -v '^$' | tr '[:upper:]' '[:lower:]' | LC_ALL=C sort -u > domains/sa-gov.txt 2>/dev/null || true
grep -v '^#' sa-banks.txt 2>/dev/null | grep -v '^$' | tr '[:upper:]' '[:lower:]' | LC_ALL=C sort -u > domains/sa-bank.txt 2>/dev/null || true
grep -v '^#' sa-services.txt 2>/dev/null | grep -v '^$' | tr '[:upper:]' '[:lower:]' | LC_ALL=C sort -u > domains/sa-services.txt 2>/dev/null || true

echo "  -> Generated $(wc -l < domains/sa.txt) unique Saudi domains"
echo "==> Done generating Saudi Arabia domain list"

# Cleanup temp files
rm -f sa-banks.txt sa-curated.txt sa-gov.txt sa-services.txt \
      sa-crux.txt sa-crux-live.txt sa-ct.txt sa-majestic.txt sa-ptr.txt sa-all-tmp.txt
