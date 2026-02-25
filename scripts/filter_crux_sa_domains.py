#!/usr/bin/env python3
"""
CrUX Top-Lists Saudi Arabia Domain Filter
==========================================
Filters the Chrome UX Report (CrUX) top-lists CSV for Saudi Arabia
to extract domains that are genuinely Saudi-hosted or Saudi-serving.

Filtering Strategy:
1. INCLUDE: All .sa TLD domains (direct match)
2. INCLUDE: Domains resolving to Saudi IP ranges (DNS check)
3. INCLUDE: Domains with Saudi-specific keywords in their name
4. EXCLUDE: Global services (google.com, facebook.com, etc.)
5. EXCLUDE: CDN/infrastructure domains
6. EXCLUDE: Adult/spam domains

The output is a clean list of Saudi domains suitable for geosite:sa.
"""

import csv
import sys
import os
import re
import socket
import ipaddress
import concurrent.futures
from urllib.parse import urlparse
from collections import defaultdict

# Saudi Arabia TLDs and sub-TLDs
SA_TLDS = {'.sa', '.com.sa', '.gov.sa', '.edu.sa', '.org.sa', '.net.sa', '.med.sa', '.sch.sa'}

# Global services to exclude (these are NOT Saudi even if popular in SA)
GLOBAL_EXCLUDES = {
    # Search & Tech Giants
    'google.com', 'google.com.sa', 'googleapis.com', 'gstatic.com', 'googleusercontent.com',
    'googlevideo.com', 'youtube.com', 'youtu.be', 'ytimg.com', 'ggpht.com',
    'google.co', 'googleadservices.com', 'googlesyndication.com', 'googletagmanager.com',
    'googleanalytics.com', 'google-analytics.com', 'doubleclick.net', 'goo.gl',
    'facebook.com', 'fb.com', 'fbcdn.net', 'instagram.com', 'meta.com', 'whatsapp.com',
    'twitter.com', 'x.com', 'twimg.com', 't.co',
    'microsoft.com', 'live.com', 'outlook.com', 'office.com', 'office365.com',
    'windows.com', 'windowsupdate.com', 'bing.com', 'msn.com', 'skype.com',
    'linkedin.com', 'github.com', 'azure.com', 'azureedge.net', 'msecnd.net',
    'apple.com', 'icloud.com', 'mzstatic.com', 'itunes.com',
    'amazon.com', 'amazonaws.com', 'cloudfront.net', 'aws.amazon.com',
    'tiktok.com', 'tiktokcdn.com', 'bytedance.com', 'musical.ly',
    'snapchat.com', 'snap.com', 'sc-cdn.net',
    'reddit.com', 'redd.it', 'redditstatic.com',
    'wikipedia.org', 'wikimedia.org', 'wiktionary.org',
    'yahoo.com', 'yimg.com',
    
    # CDN & Infrastructure
    'cloudflare.com', 'cloudflare-dns.com', 'cdnjs.cloudflare.com',
    'akamai.com', 'akamaized.net', 'akamaihd.net', 'akamaitechnologies.com',
    'fastly.net', 'fastly.com', 'fastlylb.net',
    'jsdelivr.net', 'unpkg.com', 'cdnjs.com',
    'bootstrapcdn.com', 'fontawesome.com',
    'maxcdn.com', 'stackpath.com',
    'incapsula.com', 'imperva.com',
    
    # E-commerce (Global)
    'ebay.com', 'aliexpress.com', 'alibaba.com', 'wish.com',
    
    # Streaming (Global)
    'netflix.com', 'nflxvideo.net', 'nflximg.net', 'nflxext.com',
    'spotify.com', 'scdn.co', 'spotifycdn.com',
    'twitch.tv', 'twitchcdn.net',
    'hulu.com', 'disneyplus.com', 'disney.com',
    
    # Gaming
    'steampowered.com', 'steamcommunity.com', 'steamstatic.com',
    'epicgames.com', 'unrealengine.com',
    'roblox.com', 'rbxcdn.com',
    
    # Communication
    'zoom.us', 'zoom.com', 'zoomcdn.com',
    'telegram.org', 't.me', 'telegram.me',
    'discord.com', 'discord.gg', 'discordapp.com',
    'signal.org',
    
    # Ad/Tracking
    'adsrvr.org', 'adnxs.com', 'criteo.com', 'criteo.net',
    'outbrain.com', 'taboola.com', 'pubmatic.com',
    'rubiconproject.com', 'openx.net', 'casalemedia.com',
    'moatads.com', 'doubleverify.com', 'adsafeprotected.com',
    'quantserve.com', 'scorecardresearch.com',
    'hotjar.com', 'mouseflow.com', 'crazyegg.com',
    'mixpanel.com', 'segment.com', 'amplitude.com',
    'appsflyer.com', 'adjust.com', 'branch.io',
    'onesignal.com', 'pushwoosh.com',
    
    # Fonts & Assets
    'fonts.googleapis.com', 'fonts.gstatic.com',
    'use.typekit.net', 'p.typekit.net',
    
    # Other Global
    'wordpress.com', 'wp.com', 'wordpress.org',
    'blogger.com', 'blogspot.com',
    'medium.com',
    'pinterest.com', 'pinimg.com',
    'tumblr.com',
    'quora.com',
    'stackoverflow.com', 'stackexchange.com',
    'paypal.com', 'paypalobjects.com',
    'stripe.com', 'stripe.network',
    'recaptcha.net', 'hcaptcha.com',
    'sentry.io', 'sentry-cdn.com',
    'intercom.io', 'intercomcdn.com',
    'zendesk.com', 'zdassets.com',
    'freshdesk.com', 'freshworks.com',
    'hubspot.com', 'hsforms.com', 'hubspotusercontent.com',
    'salesforce.com', 'force.com',
    'shopify.com', 'myshopify.com', 'shopifycdn.com',
    'wix.com', 'wixsite.com', 'wixstatic.com',
    'squarespace.com', 'sqspcdn.com',
    'godaddy.com', 'secureserver.net',
    'namecheap.com',
    'canva.com',
    'figma.com',
    'notion.so', 'notion.com',
    'slack.com', 'slackcdn.com',
    'trello.com',
    'dropbox.com', 'dropboxusercontent.com',
    'box.com', 'boxcdn.net',
    'onedrive.com', 'sharepoint.com',
    'drive.google.com', 'docs.google.com',
}

# Saudi-specific keywords that suggest a domain is Saudi-related
SA_KEYWORDS = {
    'saudi', 'riyadh', 'jeddah', 'jidda', 'makkah', 'mecca', 'madinah', 'medina',
    'dammam', 'khobar', 'dhahran', 'tabuk', 'taif', 'abha', 'najran', 'hail',
    'jizan', 'jazan', 'yanbu', 'jubail', 'neom', 'kaec', 'qassim', 'buraidah',
    'ksa', 'saudia', 'aramco', 'sabic', 'stc-', 'mobily', 'zain-sa',
    'alrajhi', 'alinma', 'albilad', 'sabb-', 'riyadbank', 'bankalahli',
    'tawakkalna', 'absher', 'nafath', 'sehhaty',
    'haraj', 'jarir', 'panda-sa', 'tamimi',
    'hungerstation', 'jahez', 'marsool', 'mrsool',
}

# Known Saudi companies with non-.sa domains
KNOWN_SAUDI_DOMAINS = {
    'noon.com', 'careem.com', 'hungerstation.com', 'argaam.com',
    'sabq.org', 'alarabiya.net', 'aawsat.com', 'mbc.net',
    'shahid.net', 'rotana.net', 'anghami.com', 'thmanyah.com',
    'srmg.com', 'flynas.com', 'flyadeal.com', 'almosafer.com',
    'aramex.com', 'fetchr.us', 'neom.com', 'aramco.com',
    'saudiaramco.com', 'sabic.com', 'ithra.com',
    'tawuniya.com', 'bupa.com', 'tamara.co', 'tabby.ai',
    'moyasar.com', 'tap.company', 'hyperpay.com',
    'namshi.com', 'ounass.com', 'fordeal.com',
    'bayt.com', 'adslgate.com', 'jeeny.com',
    'stcplay.gg', 'jawwy.tv',
}


def extract_domain(url):
    """Extract the registrable domain from a URL."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.path
        if not hostname:
            return None
        # Remove www. prefix
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        return hostname.lower()
    except Exception:
        return None


def get_registrable_domain(hostname):
    """Get the registrable domain (eTLD+1) from a hostname."""
    parts = hostname.split('.')
    
    # Handle .sa sub-TLDs
    if len(parts) >= 3 and parts[-1] == 'sa' and parts[-2] in ('com', 'gov', 'edu', 'org', 'net', 'med', 'sch'):
        return '.'.join(parts[-3:])
    elif len(parts) >= 2 and parts[-1] == 'sa':
        return '.'.join(parts[-2:])
    
    # Handle common two-part TLDs
    two_part_tlds = {'co.uk', 'com.au', 'co.in', 'co.jp', 'com.br', 'co.za', 'com.eg', 'com.pk', 'co.id'}
    if len(parts) >= 3:
        potential_tld = '.'.join(parts[-2:])
        if potential_tld in two_part_tlds:
            return '.'.join(parts[-3:])
    
    # Default: last two parts
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return hostname


def is_sa_tld(domain):
    """Check if domain is under .sa TLD."""
    return domain.endswith('.sa') or domain == 'sa'


def is_global_exclude(domain):
    """Check if domain is a known global service."""
    reg_domain = get_registrable_domain(domain)
    return reg_domain in GLOBAL_EXCLUDES or domain in GLOBAL_EXCLUDES


def has_sa_keyword(domain):
    """Check if domain contains Saudi-specific keywords."""
    domain_lower = domain.lower()
    for kw in SA_KEYWORDS:
        if kw in domain_lower:
            return True
    return False


def is_known_saudi(domain):
    """Check if domain is a known Saudi company."""
    reg_domain = get_registrable_domain(domain)
    return reg_domain in KNOWN_SAUDI_DOMAINS


def load_sa_ip_ranges(ip_file):
    """Load Saudi IP ranges from a CIDR file."""
    networks = []
    try:
        with open(ip_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        networks.append(ipaddress.ip_network(line, strict=False))
                    except ValueError:
                        pass
    except FileNotFoundError:
        pass
    return networks


def is_saudi_ip(ip_str, sa_networks):
    """Check if an IP address is in Saudi ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for net in sa_networks:
            if ip in net:
                return True
    except ValueError:
        pass
    return False


def resolve_domain(domain):
    """Resolve a domain to its IP addresses."""
    try:
        results = socket.getaddrinfo(domain, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = set()
        for result in results:
            ips.add(result[4][0])
        return list(ips)
    except (socket.gaierror, socket.timeout, OSError):
        return []


def filter_crux_domains(csv_file, sa_ip_file=None, output_file=None, resolve_dns=False, max_workers=50):
    """
    Main filtering function.
    
    Args:
        csv_file: Path to CrUX CSV file
        sa_ip_file: Path to Saudi IP ranges file (CIDR format)
        output_file: Path to output file
        resolve_dns: Whether to resolve DNS for non-.sa domains
        max_workers: Number of concurrent DNS resolution threads
    """
    
    # Load Saudi IP ranges
    sa_networks = load_sa_ip_ranges(sa_ip_file) if sa_ip_file else []
    
    # Read CrUX CSV
    domains = {}  # domain -> rank
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header
        for row in reader:
            if len(row) < 2:
                continue
            origin = row[0]
            try:
                rank = int(row[1])
            except ValueError:
                continue
            
            domain = extract_domain(origin)
            if not domain:
                continue
            
            # Keep the best (lowest) rank
            if domain not in domains or rank < domains[domain]:
                domains[domain] = rank
    
    print(f"Total domains in CrUX: {len(domains)}", file=sys.stderr)
    
    # Categorize domains
    sa_tld_domains = set()       # .sa TLD
    keyword_domains = set()      # Saudi keywords
    known_saudi = set()          # Known Saudi companies
    dns_saudi = set()            # Resolved to Saudi IPs
    excluded = set()             # Global services
    remaining = set()            # Need DNS check
    
    for domain, rank in domains.items():
        reg_domain = get_registrable_domain(domain)
        
        # Step 1: Include all .sa domains
        if is_sa_tld(domain):
            sa_tld_domains.add(reg_domain)
            continue
        
        # Step 2: Exclude known global services
        if is_global_exclude(domain):
            excluded.add(domain)
            continue
        
        # Step 3: Include known Saudi companies
        if is_known_saudi(domain):
            known_saudi.add(reg_domain)
            continue
        
        # Step 4: Include domains with Saudi keywords
        if has_sa_keyword(domain):
            keyword_domains.add(reg_domain)
            continue
        
        # Step 5: Remaining domains need DNS check
        remaining.add(reg_domain)
    
    print(f"  .sa TLD domains: {len(sa_tld_domains)}", file=sys.stderr)
    print(f"  Known Saudi: {len(known_saudi)}", file=sys.stderr)
    print(f"  Saudi keywords: {len(keyword_domains)}", file=sys.stderr)
    print(f"  Global excluded: {len(excluded)}", file=sys.stderr)
    print(f"  Remaining for DNS check: {len(remaining)}", file=sys.stderr)
    
    # Step 6: DNS resolution for remaining domains (if enabled)
    if resolve_dns and sa_networks:
        print(f"  Resolving DNS for {len(remaining)} domains...", file=sys.stderr)
        
        def check_domain(domain):
            ips = resolve_domain(domain)
            for ip in ips:
                if is_saudi_ip(ip, sa_networks):
                    return domain, True
            return domain, False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_domain, d): d for d in remaining}
            done = 0
            for future in concurrent.futures.as_completed(futures):
                done += 1
                if done % 1000 == 0:
                    print(f"    Resolved {done}/{len(remaining)}...", file=sys.stderr)
                try:
                    domain, is_saudi = future.result(timeout=10)
                    if is_saudi:
                        dns_saudi.add(domain)
                except Exception:
                    pass
        
        print(f"  DNS-verified Saudi: {len(dns_saudi)}", file=sys.stderr)
    
    # Combine all Saudi domains
    all_saudi = sa_tld_domains | known_saudi | keyword_domains | dns_saudi
    
    # Sort and output
    sorted_domains = sorted(all_saudi)
    
    print(f"\nTotal Saudi domains: {len(sorted_domains)}", file=sys.stderr)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"# Saudi Arabia domains from CrUX Top Lists\n")
            f.write(f"# Source: Chrome UX Report (CrUX) - Google BigQuery\n")
            f.write(f"# Filtered from {len(domains)} total domains\n")
            f.write(f"# .sa TLD: {len(sa_tld_domains)} | Known Saudi: {len(known_saudi)} | Keywords: {len(keyword_domains)} | DNS: {len(dns_saudi)}\n")
            f.write(f"# Generated by filter_crux_sa_domains.py\n\n")
            for d in sorted_domains:
                f.write(d + '\n')
        print(f"Written to {output_file}", file=sys.stderr)
    else:
        for d in sorted_domains:
            print(d)
    
    return sorted_domains


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Filter CrUX top-lists for Saudi Arabia domains')
    parser.add_argument('csv_file', help='Path to CrUX CSV file')
    parser.add_argument('-i', '--ip-file', help='Path to Saudi IP ranges file (CIDR)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--resolve-dns', action='store_true', help='Resolve DNS for non-.sa domains')
    parser.add_argument('--max-workers', type=int, default=50, help='Max DNS resolution threads')
    
    args = parser.parse_args()
    
    filter_crux_domains(
        args.csv_file,
        sa_ip_file=args.ip_file,
        output_file=args.output,
        resolve_dns=args.resolve_dns,
        max_workers=args.max_workers,
    )
