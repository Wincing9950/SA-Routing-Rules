#!/usr/bin/env python3
"""
Generate Karing App diversion rules for Saudi Arabia.
Reads the generated domain and IP lists and produces a Karing-compatible JSON config.
"""

import json
import sys
import os


def read_lines(filepath):
    """Read non-empty, non-comment lines from a file."""
    lines = []
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)
    except FileNotFoundError:
        pass
    return lines


def extract_keywords(domains, min_length=4):
    """Extract unique keywords from domain names for domain_keyword matching."""
    keywords = set()
    for domain in domains:
        # Remove TLD parts
        parts = domain.split('.')
        if len(parts) >= 2:
            # Take the main domain name (second-level domain)
            name = parts[0] if len(parts) == 2 else parts[-3] if parts[-1] == 'sa' and parts[-2] in ('com', 'gov', 'edu', 'org', 'net') else parts[0]
            if len(name) >= min_length and not name.isdigit():
                keywords.add(name)
    return sorted(keywords)


def generate_karing_config(domains_file, ipv4_file, ipv6_file, output_file):
    """Generate the Karing App JSON config."""
    
    # Read domain list
    domains = read_lines(domains_file)
    
    # Read IP ranges
    ipv4_cidrs = read_lines(ipv4_file)
    ipv6_cidrs = read_lines(ipv6_file)
    
    # Extract keywords from domains
    keywords = extract_keywords(domains)
    
    # Limit keywords to most important ones (avoid overly broad matching)
    # Keep keywords that are at least 4 chars and not too generic
    generic_words = {'www', 'http', 'https', 'mail', 'smtp', 'imap', 'pop3', 'ftp', 'dns', 'api', 'app', 'web', 'cdn', 'img', 'static', 'dev', 'test', 'beta', 'admin', 'login', 'auth', 'shop', 'store', 'blog', 'news', 'info', 'help', 'support', 'docs', 'data', 'cloud', 'host', 'server', 'node', 'edge', 'proxy', 'vpn', 'ssl', 'tls'}
    keywords = [k for k in keywords if k not in generic_words and len(k) >= 4]
    
    # Cap at 300 keywords to keep the config manageable
    if len(keywords) > 300:
        keywords = keywords[:300]
    
    config = {
        "rules": [
            {
                "outbound": "direct",
                "name": "\U0001f1f8\U0001f1e6 SA Direct",
                "switch": True,
                "or": False,
                "domain_keyword": keywords,
                "domain_regex": [
                    ".*\\.sa$",
                    "^.+\\.sa$"
                ],
                "rule_set_build_in": [
                    "geosite:sa",
                    "geosite:private",
                    "geoip:sa",
                    "geoip:private"
                ]
            },
            {
                "outbound": "direct",
                "name": "\U0001f1f8\U0001f1e6 SA-IPv4 Range",
                "switch": True,
                "or": False,
                "ip_cidr": ipv4_cidrs
            },
            {
                "outbound": "direct",
                "name": "\U0001f1f8\U0001f1e6 SA-IPv6 Range",
                "switch": True,
                "or": False,
                "ip_cidr": ipv6_cidrs
            },
            {
                "outbound": "direct",
                "name": "\U0001f1f8\U0001f1e6 Saudi Cloud & CDN",
                "switch": True,
                "or": False,
                "domain_suffix": [
                    "cloud.sa",
                    "sahara.com.sa",
                    "baianat.com.sa",
                    "saudinic.net.sa",
                    "jeraisy.com.sa",
                    "site.sa"
                ]
            },
            {
                "outbound": "direct",
                "name": "\u27a1\ufe0f Local & LAN Direct",
                "switch": True,
                "or": False,
                "ip_cidr": [
                    "0.0.0.0/8",
                    "10.0.0.0/8",
                    "100.64.0.0/10",
                    "127.0.0.0/8",
                    "169.254.0.0/16",
                    "172.16.0.0/12",
                    "192.0.0.0/24",
                    "192.168.0.0/16",
                    "224.0.0.0/4",
                    "255.255.255.255/32"
                ]
            },
            {
                "outbound": "direct",
                "name": "\u2699\ufe0f Cloudflare & Google Services",
                "switch": True,
                "or": False,
                "domain_suffix": [
                    "cloudflare.com",
                    "googletagmanager.com"
                ],
                "domain": [
                    "cloudflare.com",
                    "googletagmanager.com"
                ],
                "rule_set_build_in": [
                    "geosite:cloudflare",
                    "geoip:cloudflare"
                ]
            },
            {
                "outbound": "direct",
                "name": "\U0001f30d Direct Other Domains",
                "switch": False,
                "or": False,
                "domain_suffix": [
                    ".example.com"
                ]
            },
            {
                "outbound": "direct",
                "name": "\U0001f34f Apple (Direct)",
                "switch": True,
                "or": False,
                "rule_set_build_in": [
                    "geosite:apple-update",
                    "geosite:apple",
                    "geosite:apple-cn",
                    "geosite:apple-dev",
                    "geosite:apple-dev@cn",
                    "geosite:apple-pki",
                    "geosite:apple-pki@cn",
                    "geosite:apple@cn"
                ]
            },
            {
                "outbound": "block",
                "name": "\U0001f6ab AdBlock",
                "switch": True,
                "or": False,
                "rule_set_build_in": [
                    "geosite:category-ads",
                    "geosite:category-ads@ads",
                    "geosite:category-ads-all@ads",
                    "geosite:category-ads-all",
                    "geosite:spotify-ads",
                    "geosite:spotify-ads@ads",
                    "geosite:google@ads",
                    "geosite:apple-ads",
                    "geosite:apple-ads@ads",
                    "geosite:yahoo@ads",
                    "geosite:yahoo-ads@ads",
                    "geosite:yahoo-ads",
                    "geosite:whatsapp-ads",
                    "geosite:whatsapp-ads@ads"
                ]
            },
            {
                "outbound": "block",
                "name": "\U0001f6ab Malware",
                "switch": True,
                "or": False,
                "rule_set_build_in": [
                    "geosite:malware",
                    "geoip:malware",
                    "geoip:phishing",
                    "geosite:phishing",
                    "geosite:cryptominers"
                ]
            }
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Generated Karing config with {len(keywords)} domain keywords, {len(ipv4_cidrs)} IPv4 CIDRs, {len(ipv6_cidrs)} IPv6 CIDRs", file=sys.stderr)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Karing App config for Saudi Arabia')
    parser.add_argument('--domains', required=True, help='Path to SA domain list')
    parser.add_argument('--ipv4', required=True, help='Path to SA IPv4 CIDR list')
    parser.add_argument('--ipv6', required=True, help='Path to SA IPv6 CIDR list')
    parser.add_argument('-o', '--output', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    generate_karing_config(args.domains, args.ipv4, args.ipv6, args.output)
