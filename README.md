# 🇸🇦 Saudi Arabia Routing Rules

[![Build](https://img.shields.io/github/actions/workflow/status/Wincing9950/SA-Routing-Rules/release.yml?style=flat-square)](https://github.com/Wincing9950/SA-Routing-Rules/actions)
[![Release](https://img.shields.io/github/v/release/Wincing9950/SA-Routing-Rules?style=flat-square)](https://github.com/Wincing9950/SA-Routing-Rules/releases)
[![License](https://img.shields.io/github/license/Wincing9950/SA-Routing-Rules?style=flat-square)](LICENSE)

Enhanced geo-location routing files optimized for Saudi Arabian users, for use in **sing-box**, **V2Ray**, **Xray-core**, **Clash**, **Karing**, and all compatible clients.

Inspired by [Chocolate4U/Iran-sing-box-rules](https://github.com/Chocolate4U/Iran-sing-box-rules) and [Chocolate4U/Iran-v2ray-rules](https://github.com/Chocolate4U/Iran-v2ray-rules).

---

## Introduction

A comprehensive set of geo-location routing rules for Saudi Arabia containing:

- **GeoSite:SA** — 20,000–30,000+ Saudi Arabian domains (government, banking, telecom, e-commerce, media, apps, education)
- **GeoIP:SA** — Saudi Arabia IP CIDR blocks from RIPE NCC, BGP announcements, and MaxMind GeoLite2
- **Karing App** — Ready-to-import diversion rules config

All files are automatically rebuilt **weekly** via GitHub Actions.

---

## Download

### Rule-Set (sing-box v1.8.0+)

| Asset | GitHub Raw | jsDelivr CDN |
|-------|-----------|--------------|
| geoip-sa.srs | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/rule-set/geoip-sa.srs) | [CDN](https://cdn.jsdelivr.net/gh/Wincing9950/SA-Routing-Rules@rule-set/geoip-sa.srs) |
| geosite-sa.srs | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/rule-set/geosite-sa.srs) | [CDN](https://cdn.jsdelivr.net/gh/Wincing9950/SA-Routing-Rules@rule-set/geosite-sa.srs) |

### DAT Files (V2Ray / Xray-core)

| Asset | GitHub Raw | jsDelivr CDN |
|-------|-----------|--------------|
| geoip.dat | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/release/geoip.dat) | [CDN](https://cdn.jsdelivr.net/gh/Wincing9950/SA-Routing-Rules@release/geoip.dat) |
| geoip-lite.dat | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/release/geoip-lite.dat) | [CDN](https://cdn.jsdelivr.net/gh/Wincing9950/SA-Routing-Rules@release/geoip-lite.dat) |
| geosite.dat | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/release/geosite.dat) | [CDN](https://cdn.jsdelivr.net/gh/Wincing9950/SA-Routing-Rules@release/geosite.dat) |

### MMDB Files (Clash / sing-box)

| Asset | GitHub Raw |
|-------|-----------|
| Country.mmdb | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/release/Country.mmdb) |
| Country-lite.mmdb | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/release/Country-lite.mmdb) |

### Karing App Config

| Asset | GitHub Raw |
|-------|-----------|
| SA_Diversion_Rules_Karing_App.json | [Download](https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/release/SA_Diversion_Rules_Karing_App.json) |

---

## Usage

### sing-box v1.8.0+ (Rule-Set)

```json
{
  "outbounds": [
    { "type": "direct", "tag": "direct" },
    { "type": "selector", "tag": "proxy", "outbounds": ["..."] }
  ],
  "route": {
    "rules": [
      {
        "ip_is_private": true,
        "outbound": "direct"
      },
      {
        "rule_set": ["geosite-sa", "geoip-sa"],
        "outbound": "direct"
      }
    ],
    "rule_set": [
      {
        "tag": "geosite-sa",
        "type": "remote",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/rule-set/geosite-sa.srs"
      },
      {
        "tag": "geoip-sa",
        "type": "remote",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Wincing9950/SA-Routing-Rules/rule-set/geoip-sa.srs"
      }
    ]
  },
  "experimental": {
    "cache_file": { "enabled": true }
  }
}
```

### V2Ray / Xray-core

```json
{
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "outboundTag": "direct",
        "domain": ["geosite:sa"]
      },
      {
        "type": "field",
        "outboundTag": "direct",
        "ip": ["geoip:sa", "geoip:private"]
      }
    ]
  }
}
```

Set the assets directory:
```bash
export XRAY_LOCATION_ASSET=/path/to/your/assets/
```

### Karing App

1. Download `SA_Diversion_Rules_Karing_App.json` from the [latest release](https://github.com/Wincing9950/SA-Routing-Rules/releases)
2. In Karing App, go to **Settings** → **Diversion Rules** → **Import**
3. Select the downloaded JSON file
4. Enable the rules you want to use

### WireGuard / AmneziaWG

For WireGuard-based setups, use the IP ranges from `sa-ips/` to create split-tunnel configurations:

```ini
[Interface]
# ... your WireGuard config ...

[Peer]
# ... your peer config ...
# Exclude Saudi Arabia IPs from the tunnel (direct routing)
AllowedIPs = 0.0.0.0/0
# Then add Saudi IPs to your routing table as direct
```

Download the plain-text IP lists from the `release` branch for scripting.

---

## Data Sources

### GeoSite (20,000–30,000+ Saudi Domains)

| Source | Description | Count |
|--------|-------------|-------|
| `data/sa-domains.txt` | Major Saudi websites, telecom, e-commerce, banks, media | ~165 |
| `data/sa-gov-domains.txt` | Government portals (Absher, Tawakkalna, Nafath, ministries) | ~190 |
| `data/sa-services-domains.txt` | Saudi apps, fintech, delivery services | ~129 |
| [karenyousefi/bank-domains](https://github.com/karenyousefi/bank-domains) | Saudi bank domains | ~20 |
| `data/sa-crux-domains.txt` | CrUX Top Lists (Chrome UX Report) filtered for SA | ~11,000 |
| Certificate Transparency (crt.sh) | All .sa TLD certs + Saudi org certs | ~2,000–5,000 |
| Majestic Million | Top-1M sites filtered by TLD, keywords, DNS | ~1,000–2,000 |
| Reverse DNS PTR sweep | PTR records on Saudi IP space | ~2,000–8,000 |

### CrUX Filtering Pipeline

The Chrome UX Report (CrUX) provides the top 1M most popular domains in Saudi Arabia. Our filtering pipeline identifies Saudi domains using:

1. **TLD matching** — All `.sa` domains (7,600+)
2. **Keyword matching** — Domains containing Saudi city/brand names (3,100+)
3. **Known Saudi companies** — 200+ non-.sa domains of Saudi businesses
4. **DNS verification** — Domains resolving to Saudi IP ranges (uses dnspython for speed)

Source: [InternetHealthReport/crux-top-lists-country](https://github.com/InternetHealthReport/crux-top-lists-country) and [zakird/crux-top-lists](https://github.com/zakird/crux-top-lists)

### GeoIP

| Source | Description |
|--------|-------------|
| [RIPE NCC](https://ftp.ripe.net/pub/stats/ripencc/) | Authoritative IP delegation data for SA |
| BGP Announced Prefixes | Live BGP routing table for 10 Saudi ASes (RIPE Stat API) |
| [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) | Enhanced IP geolocation (**required** — set `MAXMIND_LICENSE_KEY` secret) |
| `data/sa-extra-ips.txt` | Verified override ranges not in RIPE/BGP data |

---

## Setup

### Step 1: Create the Repository

```bash
git clone https://github.com/Wincing9950/SA-Routing-Rules.git
# Or create a new repo and push the code
```

### Step 2: Add Secrets

Go to **Settings** → **Secrets and variables** → **Actions** and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `MAXMIND_LICENSE_KEY` | Optional | MaxMind GeoLite2 license key for enhanced GeoIP |

### Step 3: Enable Workflow Permissions

Go to **Settings** → **Actions** → **General** → **Workflow permissions** → Select **Read and write permissions**

### Step 4: Trigger First Build

Go to **Actions** → **Generate Saudi Arabia Routing Rules** → **Run workflow**

---

## Automation

| Schedule | Description |
|----------|-------------|
| Every Sunday 03:00 UTC | Full rebuild of all output files |
| Manual trigger | Available via GitHub Actions "Run workflow" button |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  GitHub Actions (Weekly)                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │ data/*.txt  │  │ RIPE NCC   │  │ CrUX Top Lists   │   │
│  │ (curated)   │  │ (SA IPs)   │  │ (Chrome UX)      │   │
│  └─────┬──────┘  └─────┬──────┘  └────────┬─────────┘   │
│        │               │                   │              │
│        ▼               ▼                   ▼              │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Build Pipeline                       │    │
│  │  • filter_crux_sa_domains.py (CrUX filter)       │    │
│  │  • generate-sa-domains.sh (domain aggregation)    │    │
│  │  • generate-sa-ips.sh (IP extraction)             │    │
│  │  • Loyalsoldier/geoip (geoip.dat + .mmdb)         │    │
│  │  • v2fly/domain-list-community (geosite.dat)      │    │
│  │  • sing-box rule-set compile (.srs)               │    │
│  │  • generate-karing-config.py (Karing JSON)        │    │
│  └──────────────────────┬───────────────────────────┘    │
│                         │                                 │
│                         ▼                                 │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Output Files                         │    │
│  │  • geoip-sa.srs / geosite-sa.srs (sing-box)      │    │
│  │  • geoip.dat / geosite.dat (v2ray/xray)           │    │
│  │  • Country.mmdb / Country-lite.mmdb (clash)        │    │
│  │  • SA_Diversion_Rules_Karing_App.json (karing)     │    │
│  └──────────────────────┬───────────────────────────┘    │
│                         │                                 │
│                         ▼                                 │
│  ┌──────────────────────────────────────────────────┐    │
│  │  GitHub Release + Branches + jsDelivr CDN         │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Contributing

All contributions are welcome! Edit files in `data/` and submit a PR:

| File | Purpose |
|------|---------|
| `data/sa-domains.txt` | Main Saudi domains |
| `data/sa-gov-domains.txt` | Government portals |
| `data/sa-services-domains.txt` | Apps and digital services |
| `data/sa-extra-ips.txt` | Additional IP ranges |

---

## License

Licensed under [GNU GPLv3](LICENSE).

---

## Acknowledgments

- [Chocolate4U/Iran-sing-box-rules](https://github.com/Chocolate4U/Iran-sing-box-rules) — Inspiration and architecture reference
- [Chocolate4U/Iran-v2ray-rules](https://github.com/Chocolate4U/Iran-v2ray-rules) — Inspiration and architecture reference
- [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) — GeoIP compilation tool
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) — GeoSite compilation tool
- [SagerNet/sing-box](https://github.com/SagerNet/sing-box) — Rule-Set compilation
- [InternetHealthReport/crux-top-lists-country](https://github.com/InternetHealthReport/crux-top-lists-country) — CrUX country data
- [zakird/crux-top-lists](https://github.com/zakird/crux-top-lists) — CrUX top lists
- [karenyousefi/bank-domains](https://github.com/karenyousefi/bank-domains) — Bank domain lists
- [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) — IP geolocation data
