# SA Entities Registry — Contribution Guide

`sa-entities.txt` is the hard-include list for non-`.sa` domains used by the
non-.sa classifier (`scripts/classify-non-sa.py`). Every domain in this file is
unconditionally included in the `geosite:sa` routing rules.

## When to add a domain here

Add a domain to `sa-entities.txt` when **all** of the following are true:

1. The domain does **not** use a `.sa` TLD — those are auto-included by the TLD check and do not belong here.
2. The domain is **not** already covered by a v2fly geosite category (run `grep -r "<domain>" v2ray-geosite/data/` to check).
3. The entity meets **at least one** of these Saudi nexus criteria:
   - Listed on Tadawul (Saudi Exchange) or majority-owned by PIF
   - Holds a SAMA licence or other Saudi regulatory approval
   - Owned or majority-funded by the Saudi government or a Saudi state entity
   - Headquartered in Saudi Arabia (verifiable via MISA record or Saudi CR number)
   - Saudi Arabia is the entity's primary or largest single market by revenue or users

## When NOT to add a domain here

- **Pan-Arab services with no SA-specific routing impact** — if a Saudi user gets the same content outside a Saudi IP, routing through SA adds no value (e.g. a pan-Arab news site with no geo-restriction).
- **Global brands with Saudi operations** — IKEA, H&M, etc. serve Saudi Arabia but are not Saudi entities. They belong in neither this file nor `sa-services-domains.txt`.
- **Parked or defunct domains** — verify the domain resolves and serves live content before adding.
- **Subdomains** — add the apex domain only (e.g. `careem.com`, not `app.careem.com`).

## Format

One domain per line. Use a section header comment for the category. Add an inline
comment with the entity name, the qualifying nexus criterion, and any Tadawul ticker
or licence number if available:

```
# Ride Hailing
careem.com # Careem (dominant SA ride/delivery; SA is largest single market)
```

## Checking a new entry

Before adding, confirm:

```bash
# 1. Domain resolves
curl -sI https://<domain> | head -1

# 2. Not already in v2fly categories
grep -r "<domain>" v2ray-geosite/data/ 2>/dev/null

# 3. Not already in sa-services-domains.txt (avoid duplicates)
grep "<domain>" data/sa-services-domains.txt
```
