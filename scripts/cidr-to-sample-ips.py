#!/usr/bin/env python3
"""
Expand CIDR blocks to a sample of IPs: one IP per /24 subnet.
Used as input for massdns PTR sweeps to keep queries manageable.

Usage: python3 cidr-to-sample-ips.py sa-ips/sa-ipv4-ripe.txt
Output: one IP per line to stdout
"""
import sys
import ipaddress


def sample_ips_from_file(filepath):
    """Yield one representative IP per /24 from each CIDR in the file."""
    seen_subnets = set()
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ':' in line:  # skip IPv6
                continue
            try:
                net = ipaddress.ip_network(line, strict=False)
            except ValueError:
                continue

            if net.version != 4:
                continue

            if net.prefixlen >= 24:
                subnet_key = str(net.network_address)
                if subnet_key not in seen_subnets:
                    seen_subnets.add(subnet_key)
                    hosts = list(net.hosts())
                    if hosts:
                        yield str(hosts[0])
            else:
                for subnet in net.subnets(new_prefix=24):
                    subnet_key = str(subnet.network_address)
                    if subnet_key not in seen_subnets:
                        seen_subnets.add(subnet_key)
                        hosts = list(subnet.hosts())
                        if hosts:
                            yield str(hosts[0])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <cidr-file>", file=sys.stderr)
        sys.exit(1)
    for ip in sample_ips_from_file(sys.argv[1]):
        print(ip)
