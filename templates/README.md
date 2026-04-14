# SA Routing Rules — Client Templates

## Quick Setup by Client

### Sing-box / Hiddify / Karing

1. Replace `YOUR_GITHUB_USER` in `singbox-full-config.json` with your GitHub username
2. Replace `YOUR_PROXY_TYPE`, `YOUR_PROXY_SERVER` with your server details
3. Import the URL or JSON as your sing-box config

Rule-set URLs (add to any existing sing-box config):
- Geosite: `https://github.com/YOUR_GITHUB_USER/SA-Routing-Rules/releases/latest/download/geosite-sa.srs`
- GeoIP:   `https://github.com/YOUR_GITHUB_USER/SA-Routing-Rules/releases/latest/download/geoip-sa.srs`

### Clash / Mihomo (Clash Verge Rev, Stash)

1. Replace `YOUR_GITHUB_USER` in `clash-full-config.yaml`
2. Replace proxy placeholders with your server details
3. Subscribe to the file URL or import directly

Rule-provider URL (add to any existing Clash config):
- `https://github.com/YOUR_GITHUB_USER/SA-Routing-Rules/releases/latest/download/sa.yaml`

### Xray-core (V2RayN, Nekoray)

1. Download `sa.dat` from the latest release
2. Place in your Xray geodata directory:
   - Windows: `%APPDATA%\v2rayN\bin\xray\`
   - Linux: `/usr/local/share/xray/`
3. In your routing rules, reference as: `ext:sa.dat:sa`

Example Xray routing rule:
```json
{
  "type": "field",
  "domain": ["ext:sa.dat:sa"],
  "outboundTag": "direct"
}
```

Alternatively, the monolithic `geosite.dat` (released alongside) contains all standard
v2fly categories plus `geosite:sa`. It can replace your existing geosite.dat entirely.
